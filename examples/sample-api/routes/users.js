const express = require("express");
const router = express.Router();

// Middleware for validation
const validateUser = (req, res, next) => {
    next();
};

// Route handlers
function getUsers(req, res) {
    res.json([{ id: 1, name: "Alice" }]);
}

function createUser(req, res) {
    res.status(201).json({ id: 2, name: req.body.name });
}

function getUserById(req, res) {
    res.json({ id: req.params.id, name: "Alice" });
}

function updateUser(req, res) {
    res.json({ id: req.params.id, updated: true });
}

function deleteUser(req, res) {
    res.status(204).send();
}

// User routes
router.get("/", getUsers);
router.post("/", validateUser, createUser);
router.get("/:id", getUserById);
router.put("/:id", updateUser);
router.delete("/:id", deleteUser);

module.exports = router;
