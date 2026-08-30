const express = require('express');
const router = express.Router();

const authenticate = (req, res, next) => next();
const authorize = (req, res, next) => next();

function listProducts(req, res) {
    res.json([]);
}

function createProduct(req, res) {
    res.status(201).json({});
}

// Router with middlewares
router.get('/', listProducts);
router.post('/', authenticate, authorize, createProduct);

// Chained route
router.route('/:id')
    .get((req, res) => res.json({}))
    .put((req, res) => res.json({}))
    .delete((req, res) => res.status(204).send());

module.exports = router;
