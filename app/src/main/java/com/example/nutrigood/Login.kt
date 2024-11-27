package com.example.nutrigood

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.data.retrofit.ApiConfig
import com.data.response.LoginRequest
import com.data.response.LoginResponse
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import android.widget.Button
import android.widget.EditText
import android.widget.TextView

class Login : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        // Inisialisasi elemen UI
        val btnLogin = findViewById<Button>(R.id.btn_login)
        val etEmail = findViewById<EditText>(R.id.email)
        val etPassword = findViewById<EditText>(R.id.password)
        val tvRegisterAccount = findViewById<TextView>(R.id.register_account)

        // Navigasi ke halaman registrasi
        tvRegisterAccount.setOnClickListener {
            val intent = Intent(this, Register::class.java)
            startActivity(intent)
        }

        // Tombol login
        btnLogin.setOnClickListener {
            val email = etEmail.text.toString().trim()
            val password = etPassword.text.toString().trim()

            Log.e("Login", "Login Button Clicked")

            // Validasi input
            if (email.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Email and password are required", Toast.LENGTH_SHORT).show()
            } else {
                // Membuat objek LoginRequest dan mengirimkan ke server
                val loginRequest = LoginRequest(email, password)
                Log.d("LoginRequest", "Request: Email=${loginRequest.getEmail()}, Password=*******") // Sembunyikan password di log
                loginUser(loginRequest)
            }
        }
    }

    private fun loginUser(request: LoginRequest) {
        val apiService = ApiConfig.getApiService()

        // Kirim permintaan login ke server
        apiService.loginUser(request).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                Log.d("LoginResponse", "Response Code: ${response.code()}")

                val loginResponse = response.body()
                if (loginResponse != null) {
                    val token = loginResponse.data?.token
                    Log.d("LoginResponse", "Token: $token")
                    if (token != null) {
                        saveToken(token)
                        startActivity(Intent(this@Login, MainActivity::class.java))
                        finish()
                    } else {
                        Log.e("LoginResponse", "Token is null")
                        Toast.makeText(this@Login, "Failed to retrieve token from server", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Log.e("LoginResponse", "Response Body is null")
                    Toast.makeText(this@Login, "Login failed: ${response.message()}", Toast.LENGTH_SHORT).show()
                }
            }


            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                Toast.makeText(this@Login, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
                Log.e("LoginError", "Error: ${t.message}")
            }
        })
    }

    private fun saveToken(token: String) {
        // Simpan token ke SharedPreferences
        val sharedPreferences = getSharedPreferences("auth", MODE_PRIVATE)
        val editor = sharedPreferences.edit()
        editor.putString("token", token)
        editor.apply()
        Log.d("SaveToken", "Token saved successfully")
    }
}
