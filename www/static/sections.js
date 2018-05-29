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
    function updateStandardSection(id, sortValue, data) {
        console.log("Calling update for section: " + holderName + " for id: " + id);
        var oldSection = $("#" + sectionName + id);
        if (data.length === 0) {
            if (oldSection.length !== 0) {
                oldSection[0].parentElement.removeChild(oldSection[0]);
            }
        }
        else {
            var section;
            if (oldSection.length === 0) {
                section = document.createElement("div");
                section.id = sectionName + id;
                var holder = $("#" + holderName);
                if (holder.length === 0)
                {
                    throw "holder " + holderName + " does not exist!";
                }
                holder.append(section);
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
        $('.' + sectionName).sort(sortCallback).appendTo('#' + holderName);
    }
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
