const express = require("express");
const usersRouter = require("./routes/users");

const app = express();

app.use(express.json());

// Health check route
app.get("/health", (req, res) => {
    res.json({ ok: true, timestamp: new Date().toISOString() });
});

// Authentication routes
app.post("/auth/login", (req, res) => {
    res.json({ token: "sample-token" });
});

// Chained route declarations
app.route("/posts")
    .get((req, res) => {
        res.json([]);
    })
    .post((req, res) => {
        res.status(201).json({ id: 1 });
    });

// Mount user sub-router
app.use("/api/users", usersRouter);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
