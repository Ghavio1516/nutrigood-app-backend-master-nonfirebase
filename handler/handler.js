const data = require('../database/database');
const bcrypt = require('bcrypt');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// Fungsi untuk menghasilkan SHA-256 hash
function generateUniqueId(email) {
    return crypto.createHash('sha256').update(email).digest('hex');
}


// Handler untuk menambahkan produk
const addProductHandler = async (request, h) => {
    const { userId } = request.auth; // Mendapatkan userId dari token JWT
    const { namaProduct, valueProduct } = request.payload;

    const createdAt = new Date().toISOString().slice(0, 19).replace('T', ' ');

    console.log('Add Product Params:', { userId, namaProduct, valueProduct, createdAt });

    try {
        const [result] = await data.query(
            'INSERT INTO products (userId, namaProduct, valueProduct, createdAt) VALUES (?, ?, ?, ?)',
            [userId, namaProduct, valueProduct, createdAt]
        );

        return h.response({
            status: 'success',
            message: 'Product added successfully',
            data: { id: result.insertId },
        }).code(201);
    } catch (error) {
        console.error('Error adding product:', error.message);
        return h.response({ status: 'fail', message: 'Failed to add product' }).code(500);
    }
};

// Handler untuk mendapatkan semua produk
const getProductsHandler = async (request, h) => {
    const { userId } = request.auth;
    console.log('Fetching products for userId:', userId); // Log userId untuk debugging
    try {
        const [rows] = await data.query(
            'SELECT * FROM products WHERE userId = ? ORDER BY createdAt DESC',
            [userId]
        );

        console.log('Fetched products:', rows);

        return h.response({
            status: 'success',
            data: {
                products: rows, // Bungkus data dalam objek `products`
            },
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to fetch products' }).code(500);
    }
};


// Handler untuk mendapatkan produk berdasarkan ID
const getProductByIdHandler = async (request, h) => {
    const { id } = request.params;

    try {
        const [rows] = await data.query(
            'SELECT * FROM products WHERE id = ?',
            [id]
        );

        if (rows.length === 0) {
            return h.response({ status: 'fail', message: 'Product not found' }).code(404);
        }

        return h.response({
            status: 'success',
            data: rows[0],
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to fetch product' }).code(500);
    }
};

// Handler untuk menghapus produk berdasarkan ID
const deleteProductByIdHandler = async (request, h) => {
    const { id } = request.params;

    try {
        const [result] = await data.query(
            'DELETE FROM products WHERE id = ?',
            [id]
        );

        if (result.affectedRows === 0) {
            return h.response({ status: 'fail', message: 'Product not found' }).code(404);
        }

        return h.response({ status: 'success', message: 'Product deleted successfully' }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to delete product' }).code(500);
    }
};

// Handler untuk mendapatkan produk hari ini
const getTodayProductsHandler = async (request, h) => {
    const { userId } = request.auth;
    const today = new Date().toISOString().slice(0, 10);

    try {
        const [rows] = await data.query(
            'SELECT * FROM products WHERE userId = ? AND DATE(createdAt) = ? ORDER BY createdAt DESC',
            [userId, today]
        );

        return h.response({
            status: 'success',
            data: rows,
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to fetch today\'s products' }).code(500);
    }
};

// Handler untuk registrasi user
const registerUserHandler = async (request, h) => {
    const { email, password, name, age, diabetes, bb } = request.payload;

    // Validasi input
    if (!email || !password || !name || typeof age === 'undefined' || typeof bb === 'undefined') {
        console.error('Missing fields:', { email, password, name, age, bb });
        return h.response({
            status: 'fail',
            message: 'All fields (email, password, name, age, bb) are required',
        }).code(400);
    }

    if (diabetes && !['yes', 'no'].includes(diabetes.toLowerCase())) {
        console.error('Invalid diabetes value:', diabetes);
        return h.response({
            status: 'fail',
            message: 'Diabetes must be either "yes" or "no"',
        }).code(400);
    }

    // Hash password
    const saltRounds = 10;
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // Generate unique identifier from email
    const userId = generateUniqueId(email);
    const createdAt = new Date().toISOString().slice(0, 19).replace('T', ' ');

    // Tetapkan nilai diabetes sebagai string
    const diabetesValue = diabetes ? diabetes.toLowerCase() === 'yes' ? 'Yes' : 'No' : 'No';

    console.log('Register User Params:', {
        userId,
        email,
        hashedPassword,
        name,
        age,
        bb,
        diabetesValue,
        createdAt,
    });

    try {
        await data.query(
            'INSERT INTO users (id, email, password, name, age, bb, diabetes, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            [userId, email, hashedPassword, name, age, bb, diabetesValue, createdAt]
        );

        return h.response({
            status: 'success',
            message: 'User registered successfully',
            data: { userId },
        }).code(201);
    } catch (error) {
        if (error.code === 'ER_DUP_ENTRY') {
            console.error('Error: Duplicate entry');
            return h.response({
                status: 'fail',
                message: 'User already exists',
            }).code(409);
        }

        console.error('Error registering user:', error.message);
        return h.response({ status: 'fail', message: `Failed to register user: ${error.message}` }).code(500);
    }
};

const getUserDetailsHandler = async (request, h) => {
    const token = request.headers.authorization?.split(' ')[1];
    if (!token) {
        return h.response({ status: 'fail', message: 'Token is missing' }).code(401);
    }

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        const userId = decoded.userId;

        console.log("Decoded UserID:", userId);

        const [rows] = await data.query('SELECT name AS username, email FROM users WHERE id = ?', [userId]);
        console.log("Database Query Result:", rows);

        if (rows.length === 0) {
            return h.response({ status: 'fail', message: 'User not found' }).code(404);
        }

        const response = {
            username: rows[0].username,
            email: rows[0].email,
        };

        return h.response(response).code(200);
    } catch (error) {
        console.error('Error fetching user details:', error.message);
        return h.response({ status: 'fail', message: 'Invalid or expired token' }).code(401);
    }
};




// Handler untuk login user
const loginUserHandler = async (request, h) => {
    const { email, password } = request.payload;

    try {
        const [rows] = await data.query(
            'SELECT * FROM users WHERE email = ?',
            [email]
        );

        if (rows.length === 0) {
            return h.response({
                status: 'fail',
                message: 'User not found',
            }).code(404);
        }

        const user = rows[0];

        // Compare hashed password
        const isValidPassword = await bcrypt.compare(password, user.password);
        if (!isValidPassword) {
            return h.response({
                status: 'fail',
                message: 'Invalid password',
            }).code(401);
        }

        // Generate token
        const token = jwt.sign(
            { userId: user.id },
            process.env.JWT_SECRET,
            { expiresIn: '1h' } // Token berlaku selama 1 jam
        );
        console.log("Generated token:", token);

        return h.response({
            status: 'success',
            message: 'Login successful',
            data: { token },
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: `Failed to login: ${error.message}` }).code(500);
    }
};

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const tf = require('@tensorflow/tfjs-node');

const uploadPhotoHandler = async (request, h) => {
    const { userId } = request.auth;
    const { base64Image } = request.payload;

    if (!base64Image) {
        console.error("Error: Missing base64Image in request payload.");
        return h.response({
            status: 'fail',
            message: 'Missing base64Image',
        }).code(400);
    }

    try {
        console.log("Starting photo upload and processing...");

        // Decode Base64 dan simpan sebagai file
        const base64Data = base64Image.split(',')[1];
        const buffer = Buffer.from(base64Data, 'base64');

        const savedFolder = path.join(__dirname, '../saved_photos');
        if (!fs.existsSync(savedFolder)) {
            console.log("Creating saved_photos directory...");
            fs.mkdirSync(savedFolder, { recursive: true });
        }

        const now = new Date();
        const time = now.toTimeString().split(' ')[0].replace(/:/g, '');
        const date = now.toISOString().slice(0, 10).replace(/-/g, '').slice(2);
        const finalFileName = `${userId}_${time}-${date}.jpg`;
        const filePath = path.join(savedFolder, finalFileName);

        fs.writeFileSync(filePath, buffer);
        console.log(`Photo saved at: ${filePath}`);

        // Eksekusi skrip OCR Python
        const scriptPath = path.join(__dirname, '../ocr_processing.py');
        console.log(`Executing Python script: ${scriptPath} with file path: ${filePath}`);

        const pythonProcess = spawn('python3', [scriptPath, filePath]);

        let scriptOutput = '';
        pythonProcess.stdout.on('data', (data) => {
            scriptOutput += data.toString();
            console.log(`Python stdout: ${data.toString()}`); // Log output
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python stderr: ${data.toString()}`); // Log errors
        });

        const ocrResult = await new Promise((resolve, reject) => {
            pythonProcess.on('close', (code) => {
                if (code === 0) {
                    try {
                        const output = JSON.parse(scriptOutput.trim());
                        if (output.message === "Berhasil" && output.nutrition_info) {
                            resolve(output.nutrition_info);
                        } else {
                            reject(new Error('OCR tidak berhasil menemukan informasi nutrisi.'));
                        }
                    } catch (error) {
                        console.error("Raw script output:", scriptOutput);
                        reject(new Error('Failed to parse script output as JSON.'));
                    }
                } else {
                    reject(new Error('Python script exited with error'));
                }
            });
        });

        console.log("OCR Result:", ocrResult);

        // Ambil data pengguna dari database
        const [userRows] = await data.query('SELECT age, bb FROM users WHERE id = ?', [userId]);
        if (userRows.length === 0) {
            throw new Error('User data not found');
        }

        const { age, bb } = userRows[0];
        console.log("User Data:", { age, bb });

        // Siapkan input untuk model
        const modelInput = {
            sajian_per_kemasan: ocrResult["Sajian per kemasan"],
            sugars: parseFloat(ocrResult["Sugars"].replace(/[^\d.]/g, '')), // Ambil angka dari "12g"
            total_sugars: parseFloat(ocrResult["Total Sugar"].replace(/[^\d.]/g, '')), // Ambil angka
            age: parseInt(age, 10),
            bb: parseFloat(bb),
        };

        console.log("Model Input:", modelInput);

        // Load dan jalankan model TensorFlow
        const modelPath = path.join(__dirname, '../model/model_Fixs_5Variabel.h5');
        const model = await tf.node.loadSavedModel(modelPath);

        const inputTensor = tf.tensor2d(
            [[
                modelInput.sajian_per_kemasan,
                modelInput.sugars,
                modelInput.total_sugars,
                modelInput.age,
                modelInput.bb,
            ]],
            [1, 5]
        );

        const prediction = model.predict(inputTensor);
        const predictionArray = prediction.dataSync();

        console.log("Model Prediction:", predictionArray);

        // Kirim hasil ke klien
        return h.response({
            status: 'success',
            message: 'Photo processed successfully',
            data: {
                nutrition_analysis: predictionArray,
            },
        }).code(200);
    } catch (error) {
        console.error('Error processing photo:', error.message);
        return h.response({
            status: 'fail',
            message: `Failed to process photo: ${error.message}`,
        }).code(500);
    }
};

// Ekspor semua handler
module.exports = {
    addProductHandler,
    registerUserHandler,
    loginUserHandler,
    getProductsHandler,
    getProductByIdHandler,
    deleteProductByIdHandler,
    getTodayProductsHandler,
    getUserDetailsHandler,
    uploadPhotoHandler,
};
