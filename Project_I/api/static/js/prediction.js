fetch("/api/prediction")

.then(response => response.json())

.then(data => {

    document.getElementById("pm25").textContent = data.pm25;

    document.getElementById("pm10").textContent = data.pm10;

    document.getElementById("aqi").textContent = data.aqi;

    document.getElementById("temp").textContent = data.temp;

});