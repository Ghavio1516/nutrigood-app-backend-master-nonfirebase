package com.example.nutrigood

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.data.retrofit.ApiConfig
import com.data.response.User
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class Register : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_register)

        // Inisialisasi elemen UI
        val etEmail = findViewById<EditText>(R.id.et_email)
        val etUsername = findViewById<EditText>(R.id.et_username)
        val etAge = findViewById<EditText>(R.id.et_age)
        val etPassword = findViewById<EditText>(R.id.et_password)
        val etConfirmPassword = findViewById<EditText>(R.id.et_confirm_password)
        val spinnerDiabetes = findViewById<Spinner>(R.id.spinner_diabetes)
        val btnSubmit = findViewById<Button>(R.id.btn_submit)

        // Set data untuk spinner
        val diabetesOptions = arrayOf("Yes", "No")
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, diabetesOptions)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        spinnerDiabetes.adapter = adapter

        // Klik tombol submit
        btnSubmit.setOnClickListener {
            val email = etEmail.text.toString().trim()
            val username = etUsername.text.toString().trim()
            val ageText = etAge.text.toString().trim()
            val password = etPassword.text.toString().trim()
            val confirmPassword = etConfirmPassword.text.toString().trim()
            val diabetesStatus = spinnerDiabetes.selectedItem.toString()

            // Validasi input
            if (email.isEmpty() || username.isEmpty() || ageText.isEmpty() || password.isEmpty() || confirmPassword.isEmpty()) {
                Toast.makeText(this, "All fields are required", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // Validasi umur (harus angka)
            val age = ageText.toIntOrNull()
            if (age == null || age <= 0) {
                Toast.makeText(this, "Age must be a valid positive number", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            if (password != confirmPassword) {
                Toast.makeText(this, "Passwords do not match", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // Panggil fungsi untuk register user
            registerUser(User(email, password, username, age, diabetesStatus))
        }
    }

    private fun registerUser(user: User) {
        val apiService = ApiConfig.getApiService()
        apiService.registerUser(user).enqueue(object : Callback<Void> {
            override fun onResponse(call: Call<Void>, response: Response<Void>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@Register, "Registration successful", Toast.LENGTH_SHORT).show()
                    startActivity(Intent(this@Register, Login::class.java))
                    finish()
                } else {
                    // Menangani respons error dari server
                    if (response.code() == 409) {
                        // Konflik: User sudah ada
                        Toast.makeText(this@Register, "User already exists. Please log in.", Toast.LENGTH_SHORT).show()
                    } else {
                        // Pesan default untuk error lainnya
                        Toast.makeText(this@Register, "Failed to register: ${response.message()}", Toast.LENGTH_SHORT).show()
                    }
                }
            }

            override fun onFailure(call: Call<Void>, t: Throwable) {
                Toast.makeText(this@Register, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

}
