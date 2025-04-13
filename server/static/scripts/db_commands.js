async function ask_llm(user_input) {
    fetch('http://127.0.0.1:5000/deepseek_test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          input: user_input
        })
    })
    .then(response => response.json())
    .then(data => {
    console.log("Response from server:", data);
    })
    .catch(error => {
    console.error("Error:", error);
    })
}