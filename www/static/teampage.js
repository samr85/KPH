
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

function requestHint(question)
{
    sendMessage("reqHint " + question);
}

function messageAdmin() {
    var message = $("#adminMessage")[0].value;
    if (!message) {
        logError("Please enter a message to send to the admins")
        return
    }
    sendMessage("messageAdmin " + message);
}

initialiseSection("question", standardSection("questionList"), []);