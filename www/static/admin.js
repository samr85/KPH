"use strict";

function mark(id, mark) {
    var teamName = $("#teamName" + id)[0];
    var questionName = $("#questionName" + id)[0];
    var correct = $("#correct" + id)[0];
    var score = $("#score" + id)[0];
    if (!(teamName && questionName && correct)) {
        errorHandler("an element doesn't exist for marking id:" + id);
        return;
    }

    var markString = "markAnswer " + teamName.value + " " + questionName.value + " " + mark;
    if (score !== undefined){
        if (!score.value) {
            errorHandler("question has custom scoring, but no score specified");
            return;
        }
        markString += " " + score.value;
    }

    if (mark !== correct.value) {
        $("<div title='Unexpected marking choice'>You've selected an unexpected response for this mark, are you sure?</div>").dialog({
            buttons: {
                "Confirm": function () {
                    $(this).dialog("close");
                    sendMessage(markString);
                },
                "Cancel": function () {
                    $(this).dialog("close");
                }
            }
        });
        return;
    }
    sendMessage(markString);
}

function messageTeam() {
    var message = $("#teamMessage")[0].value;
    var teamName = $("#teamMessageName")[0].value;
    if (!teamName) {
        logError("Please enter a team to message");
        return;
    }
    if (!message) {
        logError("Please enter a message to send to the team");
        return;
    }
    sendMessage("messageTeam " + teamName + " " + message);
}

function adjustAnswer(adjustmentType, qId, teamName, newValue)
{
    console.log(adjustmentType + " " + qId + " " + teamName + " " + newValue)
    sendMessage("adjustAnswer " + adjustmentType + " " + qId + " " + teamName + " " + newValue)
}