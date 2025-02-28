const bookQuantityDropDown = document.getElementById("quantity");
const bookTypeDropDown = document.getElementById("book-type");
const bookPrice = document.getElementById("book-price");
const bookPriceInput = document.getElementById("book-price-input");
let originalBookPrice = document.getElementById("book-price");
originalBookPrice = parseInt(originalBookPrice.innerText);
let newBookPrice;

bookTypeDropDown.addEventListener("change", updateBookPrice);
bookQuantityDropDown.addEventListener("change", updateBookPrice);

function updateBookPrice() {
  let bookTypeSelected = bookTypeDropDown.value;
  let bookQuantitySelected = bookQuantityDropDown.value;

  for (let option of bookQuantityDropDown.options) {
    option.disabled = false;
  }

  if (bookTypeSelected === "Audio-Book" || bookTypeSelected === "E-Book") {
    if (bookQuantityDropDown.value > 1) {
      bookQuantityDropDown.value = "1";
    }

    for (let option of bookQuantityDropDown.options) {
      if (option.value !== "1") {
        option.disabled = true;
      }
    }

    const percentageForEBook = 0.6;
    const percentageForAudioBook = 0.98;

    if (bookTypeSelected === "Audio-Book") {
      newBookPrice = getPercentagePrice(originalBookPrice);
      newBookPrice = Math.floor(
        newBookPrice * originalBookPrice * percentageForAudioBook
      );
      if (originalBookPrice < 300) {
        bookPrice.innerText = newBookPrice + 60;
        bookPriceInput.value = newBookPrice + 60;
      } else {
        bookPrice.innerText = newBookPrice.toLocaleString();
        bookPriceInput.value = newBookPrice;
      }
    } else {
      newBookPrice = getPercentagePrice(originalBookPrice);
      newBookPrice = Math.floor(
        newBookPrice * originalBookPrice * percentageForEBook
      );
      if (originalBookPrice > 500) {
        bookPrice.innerText = newBookPrice - 30;
        bookPriceInput.value = newBookPrice - 30;
      } else {
        bookPrice.innerText = newBookPrice.toLocaleString();
        bookPriceInput.value = newBookPrice;
      }
    }
  }

  if (bookTypeSelected === "Hardcover") {
    newBookPrice = getPercentagePrice(originalBookPrice);
    newBookPrice =
      (Math.floor(newBookPrice * originalBookPrice) + originalBookPrice) *
      bookQuantitySelected;
    bookPrice.innerText = newBookPrice.toLocaleString();
    bookPriceInput.value = newBookPrice;
  }

  if (bookTypeSelected === "Paperback") {
    newBookPrice = Math.floor(originalBookPrice * bookQuantitySelected);
    bookPrice.innerText = newBookPrice.toLocaleString();
    bookPriceInput.value = newBookPrice;
  }
}

function getPercentagePrice(originalBookPrice) {
  if (originalBookPrice <= 150) return 0.7;
  if (originalBookPrice <= 250) return 0.4;
  if (originalBookPrice <= 350) return 0.3;
  if (originalBookPrice <= 450) return 0.25;
  return 0.22;
}
