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
[type, id, version, content]. Content of "" means delete the section
update section request - requests the above, sent for each section with the wrong version after an update section list is sent
[type, id]
*/

sectionTypes = {}

class SectionType {
    constructor(name, updateFunction) {
        this.name = name;
        this.update = updateFunction;
        this.idList = {};  //List of id->version
    }
}

class SectionHolder {
    constructor(msgList) {
        var typeName = msgList.shift();
        this.id = msgList.shift();
        this.version = Number(msgList.shift());
        if (this.id == NaN || this.version == NaN) {
            throw "Invalid msglist - NaN!" + msgList.join(" ");
        }

        if (typeName in sectionTypes) {
            this.thisType = sectionTypes[typeName];
            this.idList = this.thisType.idList;
        }
        else {
            throw "Unknown section type: " + typeName;
        }
    }

    checkForUpdates() {
        if (!(this.id in this.idList) || this.idList[this.id] != this.version) {
            requestUpdateSection(this.thisType.name, this.id);
        }
    }

    update(contents) {
        this.thisType.update(this.id, contents);
        this.idList[this.id] = this.version;
    }
}

function requestSections() {
    requestUpdateSectionList(Object.keys(sectionTypes));
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
    if (msgList.length % 3)
    {
        if (msgList.length == 1)
        {
            console.log("no sections to update");
            return;
        }
        throw "invalid seciton list - not multiple of 3 entries!" + msg;
    }
    while (msgList.length)
    {
        var section = new SectionHolder(msgList);
        section.checkForUpdates();
    }
}

function requestUpdateSection(typeName, id)
{
    sendMessage(["UpdateSectionRequest", typeName, id].join(" "))
}

function updateSectionHandler(msg)
{
    //[type, id, version, content]. Content of "" means delete the section
    var msgList = msg.split(" ");
    var section = new SectionHolder(msgList);
    var contentsBase64 = msgList.shift();
    var contents = window.atob(contentsBase64);
    section.update(contents);
}

function standardSection(holderName) {
    sectionName = holderName + "Section"
    function updateStandardSection(id, data) {
        console.log("Calling update for section: " + holderName + " for id: " + id);
        oldSection = $("#" + sectionName + id)
        if (data.length === 0) {
            if (oldSection.length !== 0) {
                oldSection[0].parentElement.removeChild(oldSection[0])
            }
        }
        else {
            if (oldSection.length === 0) {
                var section = document.createElement("div");
                section.id = sectionName + id;
                section.className = sectionName;
                var holder = $("#" + holderName);
                if (holder.length === 0)
                {
                    throw "holder " + holderName + " does not exist!";
                }
                holder.append(section)
            }
            else {
                section = oldSection[0]
            }
            section.innerHTML = data;
        }
        // SORT
    }
    return updateStandardSection;
}


function initialiseSection(sectionName, updateFunction, initialMessages)
{
    console.log("Registering for section: " + sectionName)
    var section = new SectionType(sectionName, updateFunction);
    sectionTypes[sectionName] = section;
    initialMessages.forEach(function (message) {
        section.update(message["contents"]);
        section.idList[message["id"]] = message["version"];
    });
}

/*
function sectionListHandler(msg)
{
    var newIds = msg.split(" ");
    // First element is the name, rest are the IDs
    var sectionName = newIds.shift();
    sec = sectionList[sectionName]
    if (sec == undefined)
    {
        logError("section: " + sectionName + " not on page!");
        return;
    }
    var removed = sec.ids;
    console.log("Old list: " + sec.ids + "\nNew list: " + newIds)
    added = newIds.filter(function (entry) {
        idx = removed.indexOf(entry) 
        if (idx >= 0) {
            removed = removed.splice(idx, 1);
            return false;
        }
    });
    sec.ids = newIds;
    removed.forEach(sec.removeEntry)
    added.forEach(sec.addEntry)
}

function sectionRefreshHandler(msg) {
    var Ids = msg.split(" ");
    // First element is the name, rest are the IDs
    var sectionName = newIds.shift();
    sec = sectionList[sectionName]
    if (sec == undefined) {
        logError("section: " + sectionName + " not on page!");
        return;
    }
    Ids.forEach(sec.addEntry)
}

function requestSections() {
    for (sectionName in sectionList) {
        sendMessage("requestSection " + sectionName)
    }
}
*/