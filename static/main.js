$(document).ready(function () {
  setTimeout(() => {
    const bookCards = document.querySelectorAll(".book-link");

    // Check if bookCards is not null and is a NodeList
    if (bookCards) {
      bookCards.forEach((card) => {
        card.addEventListener("click", () => {
          const bookTitle = card.querySelector(".book-title").textContent;
          const bookAuthor = card.querySelector(".book-author").textContent;
          const bookImgUrl = card
            .querySelector(".books-img")
            .getAttribute("src");

          fetchBookSummary(bookTitle, bookAuthor, bookImgUrl, "#");
        });
      });
    } else {
      console.log("No book cards found.");
    }
  }, 1000);

  function fetchBookSummary(bookTitle, bookAuthor, bookImgUrl, destinationUrl) {
    $.get("/get_book_summary", { title: bookTitle }, (data) => {
      if (data.error) {
        $("#window-title").text(bookTitle);
        console.log(bookTitle);
        $("#window-author").text(bookAuthor);
        $("#window-summary").text("Sorry! No, Summary Available");
        $("#window-book-img").attr("src", bookImgUrl);
        showModalNearUser();
        $(".window-popper").show();
      } else {
        $("#window-title").text(bookTitle);
        $("#window-author").text(bookAuthor);
        $("#window-summary").text(data.summary);
        $("#window-book-img").attr("src", bookImgUrl);
        $("#buy-now-btn").attr("href", "/buynow/" + bookTitle);
        // $("#buy-now-btn").attr("href", data.amazonUrl);
        showModalNearUser();
        $(".window-popper").show();
      }
    });
  }

  const closeBtn = document.querySelector(".window-close");
  const windowPop = document.querySelector(".window-popper");

  closeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    $(".window-popper").hide();
  });

  function showModalNearUser() {
    const userPosition = $(window).scrollTop() + $(window).height() / 2;
    const modalHeight = $("#window").height();
    const modalTop = Math.min(userPosition - modalHeight / 2 - 100);
    console.log(modalTop + " " + userPosition);

    $("#window").css("top", modalTop + "px");
    $(".window-popper").css("height", $(".modal").height() + 50 + "px");
    $(".window-container").css("height", $(".modal").height() + 50 + "px");
  }
});
