'use strict';
/*
list of section types:
type id
update function (update with no data is delete)

list of current sections:
section type, id, version

messages:
update section list - sends through new section list
[[type, id, version]]
update section list request - requests above.  Sent after messaging initial connect and reconnect
[[type]]
update seciton - updates a specific section
[type, id, version, sortId, content]. Content of "" means delete the section
update section request - requests the above, sent for each section with the wrong version after an update section list is sent
[type, id]
*/

var sectionTypes = new Map();

class SectionType {
    constructor(name, updateFunction) {
        this.name = name;
        this.update = updateFunction;
        this.idList = {};    //List of id->version
        this.oldIdList = {}; //A list to be used while updating to ensure that old entries that shouldn't exist any more are removed
    }
}

class SectionHolder {
    constructor(msgList) {
        var typeName = msgList.shift();
        this.id = msgList.shift();
        this.version = Number(msgList.shift());
        if (isNaN(this.id) || isNaN(this.version)) {
            throw "Invalid msglist - NaN!" + msgList.join(" ");
        }

        if (sectionTypes.has(typeName)) {
            this.thisType = sectionTypes.get(typeName);
            this.idList = this.thisType.idList;
        }
        else {
            throw "Unknown section type: " + typeName;
        }
        /* was this ID know about before? */
        if (this.id in this.thisType.oldIdList) {
            delete this.thisType.oldIdList[this.id];
        }
    }

    checkForUpdates() {
        if (!(this.id in this.idList) || this.idList[this.id] !== this.version) {
            requestUpdateSection(this.thisType.name, this.id);
        }
    }

    update(sortValue, contents) {
        this.thisType.update(this.id, sortValue, contents);
        this.idList[this.id] = this.version;
        if (window.postSectionUpdate !== undefined) {
            window.postSectionUpdate();
        }
    }
}

function requestSections() {
    requestUpdateSectionList(Array.from(sectionTypes.keys()));
}

function requestUpdateSectionList(typeNames) {
    if (typeNames.length) {
        sendMessage((["UpdateSectionListRequest"].concat(typeNames)).join(" "));
    }
}

function updateSectionListHandler(msg)
{
    //Messages of format: [[type, id, version]]
    var msgList = msg.split(" ");
    if (msgList.length === 1) {
        // an empty string still comes out with an array of 1 entry...
        // An empty list means to clear all sections
        msgList.shift();
    }
    if (msgList.length % 3)
    {
        throw "invalid seciton list - not multiple of 3 entries!" + msg;
    }

    sectionTypes.forEach(function (st) {
        st.oldIdList = st.idList;
        st.idList = {};
        console.log("Created oldIdList for:");
        console.log(st);
    });
    while (msgList.length)
    {
        var section = new SectionHolder(msgList);
        section.checkForUpdates();
    }
    /*Remove no longer existing sections*/
    sectionTypes.forEach(function (st) {
        Object.keys(st.oldIdList).forEach(function (badId) {
            console.log("Removing old section: " + st.name + " " + badId);
            st.update(badId, 0, "");
        });
    });
}

function requestUpdateSection(typeName, id)
{
    sendMessage(["UpdateSectionRequest", typeName, id].join(" "));
}

function updateSectionHandler(msg)
{
    //[type, id, version, content]. Content of "" means delete the section
    var msgList = msg.split(" ");
    var section = new SectionHolder(msgList);
    var sortValue = msgList.shift();
    var contentsBase64 = msgList.shift();
    var contents = window.atob(contentsBase64);
    section.update(sortValue, contents);
}

function sortCallback(a, b) { return $(a).data('sort') > $(b).data('sort'); }

function standardSection(holderName, modifySectionCallback = undefined) {
    var sectionName = holderName + "Section";
    // These 2 vars can't be filled in until we finish loading the page
    var emptyDiv = undefined;
    var holder = undefined;
    function updateStandardSection(id, sortValue, data) {
        console.log("Calling update for section: " + holderName + " for id: " + id);
        var oldSection = $("#" + sectionName + id);
        if (data.length === 0) {
            if (oldSection.length !== 0) {
                holder.removeChild(oldSection[0]);
            }
        }
        else {
            var section;
            if (oldSection.length === 0) {
                section = document.createElement("div");
                section.id = sectionName + id;
                holder.appendChild(section);
            }
            else {
                section = oldSection[0];
            }
            section.className = sectionName;
            section.innerHTML = data;
            $(section).data('sort', sortValue);
            if (modifySectionCallback) {
                modifySectionCallback(section);
            }
        }
        // SORT
        var children = $('.' + sectionName);
        if (children.length === 0) {
            holder.appendChild(emptyDiv);
        } else {
            if (emptyDiv.parentNode === holder) {
                holder.removeChild(emptyDiv);
            }
            children.sort(sortCallback).appendTo('#' + holderName);
        }
    }
    // At end of page load, look at the contents of the parent div, wrap that in a div, and save it off as
    //  the html that should be displayed whenever there is nothing else there
    $(function () {
        var holderJQ = $("#" + holderName);
        if (holderJQ.length !== 1) {
            throw "holder " + holderName + " does not exist!";
        }
        holder = holderJQ[0];
        emptyDiv = $("<dev>" + holder.innerHTML + "<div>")[0];
        holder.innerHTML = "";
        holder.appendChild(emptyDiv);
    });
    return updateStandardSection;
}

function initialiseSection(sectionName, updateFunction, initialMessages)
{
    console.log("Registering for section: " + sectionName);
    var section = new SectionType(sectionName, updateFunction);
    sectionTypes.set(sectionName, section);
    initialMessages.forEach(function (message) {
        section.update(message["contents"]);
        section.idList[message["id"]] = message["version"];
    });
}

var sectionDisplays = new Map();
function chechSectionToggle(identifier, speed = 0)
{
    if (sectionDisplays.has(identifier))
    {
        $("." + identifier + "triangle").removeClass("ui-icon-triangle-1-s").addClass("ui-icon-triangle-1-e")
        $("." + identifier).slideUp(speed)
    }
    else
    {
        $("." + identifier + "triangle").removeClass("ui-icon-triangle-1-e").addClass("ui-icon-triangle-1-s")
        $("." + identifier).slideDown(speed)
    }
}
function toggleSection(identifier)
{
    if (sectionDisplays.has(identifier))
    {
        sectionDisplays.delete(identifier);
    }
    else
    {
        sectionDisplays.set(identifier, true);
    }
    chechSectionToggle(identifier, 200);
}

function standardSectionCheckToggle(holderName, modifySectionCallback = undefined) {
    var mainFn = standardSection(holderName, modifySectionCallback);
    function updateStandardSectionCheckToggle(id, sortValue, data){
        mainFn(id, sortValue, data);
        for (const identifier of sectionDisplays.keys()){
            chechSectionToggle(identifier);
        }
    }
    return updateStandardSectionCheckToggle;
}
