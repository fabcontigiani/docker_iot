document.addEventListener('DOMContentLoaded', function() {
  const destelloRadio = document.getElementById('optionsRadios1');
  const setpointRadio = document.getElementById('optionsRadios2');
  const tempContainer = document.getElementById('temperatura-container');
  const rangeInput = document.getElementById('customRange3');
  const rangeValue = document.getElementById('range-value');

  function updateRangeState() {
    // Hide if "Destello" is selected, show if "Setpoint" is selected
    tempContainer.style.display = destelloRadio.checked ? 'none' : '';
  }

  function updateRangeValue() {
    rangeValue.textContent = rangeInput.value;
  }

  destelloRadio.addEventListener('change', updateRangeState);
  setpointRadio.addEventListener('change', updateRangeState);

  rangeInput.addEventListener('input', updateRangeValue);

  // Set initial state on page load
  updateRangeState();
  updateRangeValue();
});