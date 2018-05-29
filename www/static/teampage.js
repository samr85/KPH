
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
    $("<div title='Requesting hint'>Requesting this hint will reduce the value of this question by " + value + "points, are you sure you want to do this ?</div > ").dialog({
        buttons: {
            "Confirm": function () {
                $(this).dialog("close");
                sendMessage("reqHint " + question);
            },
            "Cancel": function () {
                $(this).dialog("close");
            }
        }
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

initialiseSection("question", standardSection("questionList"), []);
