async function fetchSystemState() {
    try {
        const response = await fetch('http://127.0.0.1:5000/fetch_state', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });
        const state = await response.json();
        if(response.ok && state){
            ps_state = state;
        }
    }   catch (error) {
        console.error("Error:", error);
    }
}