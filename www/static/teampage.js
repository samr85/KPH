
function submitAnswer(question)
{
    if ($("#" + question + "Answer")[0].value)
    {
        sendMessage("subAnswer " + question + " " + $("#" + question + "Answer")[0].value)
    }
    else
    {
        $("#" + question + "Err")[0].innerHTML = "Error: Please enter an answer to submit"
    }
}

function requestHint(question)
{
    sendMessage("reqHint " + question)
}

initialiseSection("question", standardSection("questionList"), [])