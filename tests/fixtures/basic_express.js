const express = require('express');
const app = express();

function getUsers(req, res) {
    res.json([]);
}

function createUser(req, res) {
    res.status(201).json({});
}

function updateUser(req, res) {
    res.json({});
}

function patchUser(req, res) {
    res.json({});
}

function deleteUser(req, res) {
    res.status(204).send();
}

app.get('/users', getUsers);
app.post('/users', createUser);
app.put('/users/:id', updateUser);
app.patch('/users/:id', patchUser);
app.delete('/users/:id', deleteUser);
app.options('/users', (req, res) => res.sendStatus(200));
app.head('/users', (req, res) => res.sendStatus(200));
app.all('/status', (req, res) => res.send('OK'));

app.listen(3000);
