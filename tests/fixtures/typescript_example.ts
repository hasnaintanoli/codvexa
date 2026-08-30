import { Router, Request, Response } from 'express';

interface UserParams {
    id: string;
}

interface CreateUserBody {
    name: string;
    email: string;
}

const router: Router = Router();

router.get('/items', (req: Request, res: Response): void => {
    res.json([{ id: 1, name: 'Item 1' }]);
});

router.post<UserParams, {}, CreateUserBody>('/items', async (req: Request, res: Response): Promise<void> => {
    res.status(201).json({ id: 2, name: req.body.name });
});

router.delete('/items/:id', (req: Request, res: Response): void => {
    res.status(204).send();
});

export default router;
