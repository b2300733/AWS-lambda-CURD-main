// ==========================================
// API Gateway URL
// ==========================================

// Replace this with your API Gateway URL

const API_BASE_URL =
    window.PRODUCT_CONFIG && window.PRODUCT_CONFIG.API_GW_BASE_URL_STR;
const API_URL = API_BASE_URL
    ? API_BASE_URL.replace(/\/$/, "") + "/items"
    : null;
const LOCAL_STORAGE_KEY = "computer-products";
const dataSource = document.getElementById("dataSource");

function setDataSource(message) {
    dataSource.textContent = message;
}

// ==========================================
// Load products when page opens
// ==========================================

loadProducts();

// ==========================================
// READ - Get all products
// ==========================================

async function loadProducts() {
    try {
        if (!API_URL) {
            let products = JSON.parse(
                localStorage.getItem(LOCAL_STORAGE_KEY) || "null",
            );
            if (!products) {
                const response = await fetch("products.json");
                if (!response.ok) {
                    throw new Error("Failed to load products.json");
                }
                products = await response.json();
                localStorage.setItem(
                    LOCAL_STORAGE_KEY,
                    JSON.stringify(products),
                );
            }
            setDataSource(
                "Data source: local browser storage (API Gateway is not configured).",
            );
            displayProducts(products);
            return;
        }

        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Failed to load products");
        }

        const products = await response.json();

        setDataSource("Data source: API Gateway " + API_URL);
        displayProducts(Array.isArray(products) ? products : products.items);
    } catch (error) {
        console.error(error);

        setDataSource("Unable to load products: " + error.message);
        alert("Failed to load products: " + error.message);
    }
}

// ==========================================
// Display products in table
// ==========================================

function displayProducts(products) {
    const table = document.getElementById("productTable");

    table.innerHTML = "";

    products.forEach((product) => {
        const row = document.createElement("tr");

        const idCell = document.createElement("td");

        const nameCell = document.createElement("td");

        const priceCell = document.createElement("td");

        const actionCell = document.createElement("td");

        // ID
        idCell.textContent = product.id;

        // Name
        nameCell.textContent = product.name;

        // Price
        priceCell.textContent = Number(product.price).toFixed(2);

        // Edit button
        const editButton = document.createElement("button");

        editButton.textContent = "Edit";

        editButton.addEventListener("click", function () {
            editProduct(product.id, product.name, product.price);
        });

        // Delete button
        const deleteButton = document.createElement("button");

        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", function () {
            deleteProduct(product.id);
        });

        actionCell.appendChild(editButton);

        actionCell.appendChild(document.createTextNode(" "));

        actionCell.appendChild(deleteButton);

        row.appendChild(idCell);
        row.appendChild(nameCell);
        row.appendChild(priceCell);
        row.appendChild(actionCell);

        table.appendChild(row);
    });
}

// ==========================================
// CREATE / UPDATE
// ==========================================

document
    .getElementById("productForm")
    .addEventListener("submit", async function (event) {
        event.preventDefault();

        const id = document.getElementById("productId").value;

        const name = document.getElementById("name").value;

        const price = document.getElementById("price").value;

        try {
            let response;

            if (!API_URL) {
                const products = JSON.parse(
                    localStorage.getItem(LOCAL_STORAGE_KEY) || "[]",
                );
                const product = {
                    id: id
                        ? Number(id)
                        : products.reduce(
                              (highestId, item) =>
                                  Math.max(highestId, Number(item.id)),
                              0,
                          ) + 1,
                    name: name,
                    price: Number(price),
                };
                const index = products.findIndex(
                    (item) => Number(item.id) === Number(id),
                );
                if (index >= 0) {
                    products[index] = product;
                } else {
                    products.push(product);
                }
                localStorage.setItem(
                    LOCAL_STORAGE_KEY,
                    JSON.stringify(products),
                );
                resetForm();
                await loadProducts();
                return;
            }

            // ==================================
            // UPDATE PRODUCT
            // ==================================

            if (id) {
                response = await fetch(API_URL + "/" + id, {
                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json",
                    },

                    body: JSON.stringify({
                        name: name,
                        price: Number(price),
                    }),
                });
            }

            // ==================================
            // CREATE PRODUCT
            // ==================================
            else {
                response = await fetch(API_URL, {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                    },

                    body: JSON.stringify({
                        name: name,
                        price: Number(price),
                    }),
                });
            }

            if (!response.ok) {
                let errorMessage = "Request failed";
                try {
                    const error = await response.json();
                    errorMessage = error.message || errorMessage;
                } catch (parseError) {
                    console.error(
                        "Unable to parse API error response",
                        parseError,
                    );
                }
                throw new Error(errorMessage);
            }

            resetForm();
            await loadProducts();
        } catch (error) {
            console.error(error);

            alert(
                "Save failed. Check that API Gateway has been deployed and has CORS enabled. " +
                    error.message,
            );
        }
    });

// ==========================================
// EDIT PRODUCT
// ==========================================

function editProduct(id, name, price) {
    document.getElementById("productId").value = id;

    document.getElementById("name").value = name;

    document.getElementById("price").value = price;

    document.getElementById("submitButton").textContent = "Update Product";

    document.getElementById("cancelButton").style.display = "inline-block";
}

function resetForm() {
    document.getElementById("productForm").reset();
    document.getElementById("productId").value = "";
    document.getElementById("submitButton").textContent = "Add Product";
    document.getElementById("cancelButton").style.display = "none";
}

// ==========================================
// CANCEL EDIT
// ==========================================

document.getElementById("cancelButton").addEventListener("click", function () {
    resetForm();
});

// ==========================================
// DELETE PRODUCT
// ==========================================

async function deleteProduct(id) {
    if (!confirm("Delete this product?")) {
        return;
    }

    try {
        if (!API_URL) {
            const products = JSON.parse(
                localStorage.getItem(LOCAL_STORAGE_KEY) || "[]",
            ).filter((product) => Number(product.id) !== Number(id));
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(products));
            await loadProducts();
            return;
        }

        const response = await fetch(API_URL + "/" + id, {
            method: "DELETE",
        });

        if (!response.ok) {
            const error = await response.json();

            throw new Error(error.message || "Delete failed");
        }

        await loadProducts();
    } catch (error) {
        console.error(error);

        alert(
            "Delete failed. Check that API Gateway has been deployed and has CORS enabled. " +
                error.message,
        );
    }
}
