
function submitAnswer(question)
{
    if ($("#" + question + "Answer")[0].value)
    {
        sendMessage("subAnswer " + question + " " + window.btoa($("#" + question + "Answer")[0].value));
    }
    else
    {
        logError("Please enter an answer to submit");
    }
}

function requestHint(question, value)
{
    var valueStr = value + "point";
    if (value !== 1)
    {
        valueStr += "s";
    }

    if ($('#hintRequest').length)
    {
        return;
    }

    $("<div id='hintRequest' title='Requesting hint'>Requesting this hint will reduce the value of this question by " + valueStr + ", are you sure?</div>").dialog({
        buttons: {
            "Yes": function () {
                $(this).dialog("destroy");
                sendMessage("reqHint " + question);
            },
            "No": function () {
                $(this).dialog("destroy");
            }
        },
        modal: true
    });
}

function messageAdmin() {
    var message = $("#adminMessage")[0].value;
    if (!message) {
        logError("Please enter a message to send to the admins");
        return;
    }
    sendMessage("messageAdmin " + message);
}

initialiseSection("question", standardSectionCheckToggle("questionList"), []);
initialiseSection("penalty", standardSection("penaltyDiv"), []);
