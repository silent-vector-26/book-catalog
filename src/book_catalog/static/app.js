const message = document.querySelector("#message");
const bookForm = document.querySelector("#book-form");
const authorForm = document.querySelector("#author-form");

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const details = Array.isArray(body?.detail)
      ? body.detail.map((item) => item.msg).join("; ")
      : body?.detail;
    throw new Error(details || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function showMessage(text = "") {
  message.textContent = text;
}

function addAction(row, label, action, destructive = false) {
  let cell = row.querySelector(".actions");
  if (!cell) {
    cell = row.insertCell();
    cell.className = "actions";
  }
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.classList.toggle("delete-button", destructive);
  button.addEventListener("click", action);
  cell.append(button);
}

function makeCell(row, value) {
  row.insertCell().textContent = value ?? "";
}

async function loadBooks() {
  const [books, authors] = await Promise.all([
    api("/api/books/summary"),
    api("/api/authors"),
  ]);
  const table = document.querySelector("#books-table");
  const authorSelect = document.querySelector("#book-author");
  table.replaceChildren();
  authorSelect.replaceChildren();

  for (const author of authors) {
    const option = document.createElement("option");
    option.value = author.id;
    option.textContent = author.name;
    authorSelect.append(option);
  }

  for (const book of books) {
    const row = table.insertRow();
    makeCell(row, book.title);
    makeCell(row, book.author);
    makeCell(row, book.year ?? "—");
    makeCell(row, `$${book.price}`);
    addAction(row, "Edit", () => editBook(book.id));
    addAction(row, "Delete", () => removeBook(book.id), true);
  }
  document.querySelector("#books-empty").classList.toggle("hidden", books.length > 0);
  document.querySelector("#add-book").disabled = authors.length === 0;
  document.querySelector("#add-book").title =
    authors.length === 0 ? "Add an author before creating a book" : "";
}

async function loadAuthors() {
  const authors = await api("/api/authors");
  const table = document.querySelector("#authors-table");
  table.replaceChildren();
  for (const author of authors) {
    const row = table.insertRow();
    makeCell(row, author.name);
    makeCell(row, author.country || "—");
    addAction(row, "Edit", () => editAuthor(author));
    addAction(row, "Delete", () => removeAuthor(author.id), true);
  }
  document.querySelector("#authors-empty").classList.toggle("hidden", authors.length > 0);
}

async function refresh() {
  showMessage();
  try {
    await Promise.all([loadBooks(), loadAuthors()]);
  } catch (error) {
    showMessage(error.message);
  }
}

function resetForm(form) {
  form.reset();
  form.classList.add("hidden");
}

async function editBook(id) {
  try {
    const book = await api(`/api/books/${id}`);
    document.querySelector("#book-id").value = book.id;
    document.querySelector("#book-title").value = book.title;
    document.querySelector("#book-year").value = book.year ?? "";
    document.querySelector("#book-price").value = book.price;
    document.querySelector("#book-author").value = book.author_id;
    document.querySelector("#book-form-heading").textContent = "Edit book";
    bookForm.classList.remove("hidden");
    document.querySelector("#book-title").focus();
  } catch (error) {
    showMessage(error.message);
  }
}

function editAuthor(author) {
  document.querySelector("#author-id").value = author.id;
  document.querySelector("#author-name").value = author.name;
  document.querySelector("#author-country").value = author.country ?? "";
  document.querySelector("#author-form-heading").textContent = "Edit author";
  authorForm.classList.remove("hidden");
  document.querySelector("#author-name").focus();
}

async function removeBook(id) {
  if (!window.confirm("Delete this book?")) return;
  try {
    await api(`/api/books/${id}`, { method: "DELETE" });
    await refresh();
  } catch (error) {
    showMessage(error.message);
  }
}

async function removeAuthor(id) {
  if (!window.confirm("Delete this author?")) return;
  try {
    await api(`/api/authors/${id}`, { method: "DELETE" });
    await refresh();
  } catch (error) {
    showMessage(error.message);
  }
}

document.querySelectorAll(".nav-button").forEach((button) => {
  button.addEventListener("click", () => {
    const showBooks = button.dataset.view === "books";
    document.querySelector("#books-view").classList.toggle("hidden", !showBooks);
    document.querySelector("#authors-view").classList.toggle("hidden", showBooks);
    document.querySelectorAll(".nav-button").forEach((item) =>
      item.classList.toggle("active", item === button),
    );
    showMessage();
  });
});

document.querySelector("#add-book").addEventListener("click", () => {
  bookForm.reset();
  document.querySelector("#book-id").value = "";
  document.querySelector("#book-form-heading").textContent = "Add a book";
  bookForm.classList.remove("hidden");
});

document.querySelector("#add-author").addEventListener("click", () => {
  authorForm.reset();
  document.querySelector("#author-id").value = "";
  document.querySelector("#author-form-heading").textContent = "Add an author";
  authorForm.classList.remove("hidden");
});

document.querySelectorAll("[data-cancel]").forEach((button) => {
  button.addEventListener("click", () =>
    resetForm(button.dataset.cancel === "book" ? bookForm : authorForm),
  );
});

bookForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#book-id").value;
  const year = document.querySelector("#book-year").value;
  const payload = {
    title: document.querySelector("#book-title").value,
    year: year ? Number(year) : null,
    price: document.querySelector("#book-price").value,
    author_id: Number(document.querySelector("#book-author").value),
  };
  try {
    await api(id ? `/api/books/${id}` : "/api/books", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    resetForm(bookForm);
    await refresh();
  } catch (error) {
    showMessage(error.message);
  }
});

authorForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#author-id").value;
  const country = document.querySelector("#author-country").value.trim();
  const payload = {
    name: document.querySelector("#author-name").value,
    country: country || null,
  };
  try {
    await api(id ? `/api/authors/${id}` : "/api/authors", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    resetForm(authorForm);
    await refresh();
  } catch (error) {
    showMessage(error.message);
  }
});

refresh();
