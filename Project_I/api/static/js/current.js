fetch("/api/current")

.then(response => response.json())

.then(data => {

    document.getElementById("pm25").textContent = data.pm25;

    document.getElementById("pm10").textContent = data.pm10;

    document.getElementById("aqi").textContent = data.aqi;

    document.getElementById("temp").textContent = data.temp;

    document.getElementById("humidity").textContent = data.humidity;

    document.getElementById("windspeed").textContent = data.windspeed;

    document.getElementById("visibility").textContent = data.visibility;

    document.getElementById("pressure").textContent = data.sealevelpressure;

});