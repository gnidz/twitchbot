const startBtn = document.querySelector('.spinner__start-button');
const input = document.querySelector('.spinner__input');
let plate = document.querySelector('.spinner__plate');
let items = [...document.getElementsByClassName('spinner__item')];
let countdownTimer;

// Fetch values from JSON file
async function loadValues() {
    try {
        const response = await fetch('../giveaway.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        return [];
    }
}

async function loadWinner() {
    try {
        const response = await fetch('../winner.json'); // Adjust path as needed
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data || 'No winner yet';
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        return 'Error loading winner';
    }
}

// Initialize input with values from JSON
async function initializeInput() {
    const values = await loadValues();
    if (values.length > 0) {
        input.max = values.length;
        input.value = Math.min(input.value, input.max); // Ensure current value is within bounds
    }
}

input.addEventListener('change', () => {
    if (input.value === '' || +input.value < 1) {
        input.value = 1;
    }
    if (+input.value > input.max) {
        input.value = input.max;
    }
});

startBtn.addEventListener('click', startCountdown);

// Automatically start countdown on page load
window.addEventListener('load', startCountdown);

function startCountdown() {
    let countdown = 5; // 5 seconds countdown
    startBtn.textContent = countdown; // Display countdown on button
    startBtn.disabled = true; // Disable button during countdown
    startBtn.classList.add('countdown-active'); // Add the countdown-active class

    countdownTimer = setInterval(() => {
        countdown--;
        startBtn.textContent = countdown;
        if (countdown <= 0) {
            clearInterval(countdownTimer);
            startBtn.textContent = 'GO!'; // Reset button text
            startBtn.disabled = false; // Enable button after countdown
            startBtn.classList.remove('countdown-active'); // Remove the countdown-active class
            randomizeItems();
            if (!plate.classList.contains('spinner__plate--spin')) {
                plate.classList.add('spinner__plate--spin');
            } else {
                const newPlate = plate.cloneNode(true);
                plate.parentNode.replaceChild(newPlate, plate);
                plate = newPlate;
                items = [...document.getElementsByClassName('spinner__item')];
            }
        }
    }, 1000); // Update every second
}

async function randomizeItems() {
    try {
        const values = await loadValues(); // Fetch values from JSON file
        const winner = await loadWinner(); // Fetch winner from JSON file // Find the index of the winner
        // Set the winner value
        items[0].textContent = winner;

        // Create a shallow copy of the values array to modify
        let availableValues = [...values];

        // Remove the winner from the available values array
        availableValues = availableValues.filter(val => val !== winner);

        // Iterate through the items
        items.forEach(item => {
            // Randomize items only if the item is not the winner
            if (item.textContent !== winner) {
                // Select a random index from the available values
                const randIndex = random(0, availableValues.length - 1);
                // Assign the value to the item
                item.textContent = availableValues[randIndex];
                // Remove the assigned value from availableValues to prevent duplicates
                availableValues.splice(randIndex, 1);
            } else {
                // Ensure the winner item is displayed as the winner
                item.textContent = winner;
        }
    });

    } catch (error) {
        console.error('Error in randomizing items:', error);
    }
}


function random(min, max) {
    return Math.floor(min + Math.random() * (max - min + 1));
}

// Initialize input on page load
initializeInput();
