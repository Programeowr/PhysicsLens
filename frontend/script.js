async function generateDiagram() {

    const problemText = document.getElementById("problemInput").value;

    const response = await fetch("http://127.0.0.1:8000/solve-and-diagram", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            problem: problemText
        })
    });

    if (!response.ok) {
        alert("Error generating diagram");
        return;
    }

    const svgText = await response.text();

    document.getElementById("diagramContainer").innerHTML = svgText;
}