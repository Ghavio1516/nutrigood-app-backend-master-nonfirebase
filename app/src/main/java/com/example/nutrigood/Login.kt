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

        // Cek apakah user sudah login
        if (isUserLoggedIn()) {
            navigateToMainActivity(showScanFragment = true)
            finish()
            return
        }

        setContentView(R.layout.activity_login)

        // Inisialisasi elemen UI
        val btnLogin = findViewById<Button>(R.id.btn_login)
        val etEmail = findViewById<EditText>(R.id.email)
        val etPassword = findViewById<EditText>(R.id.password)
        val tvRegisterAccount = findViewById<TextView>(R.id.register_account)
        val tvAboutUs = findViewById<TextView>(R.id.about_us)

        tvRegisterAccount.setOnClickListener {
            val intent = Intent(this, Register::class.java)
            startActivity(intent)
        }
        tvAboutUs.setOnClickListener {
            val intent = Intent(this, AboutUs::class.java)
            startActivity(intent)
        }

        // Tombol login
        btnLogin.setOnClickListener {
            val email = etEmail.text.toString().trim()
            val password = etPassword.text.toString().trim()

            if (email.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Email and password are required", Toast.LENGTH_SHORT).show()
            } else if (etEmail.error != null) {
                Toast.makeText(this, "Email tidak valid", Toast.LENGTH_SHORT).show()
            } else {
                val loginRequest = LoginRequest(email, password)
                loginUser(loginRequest)
            }
        }
    }

    private fun loginUser(request: LoginRequest) {
        val apiService = ApiConfig.getApiService()

        // Kirim permintaan login ke server
        apiService.loginUser(request).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                val loginResponse = response.body()
                if (loginResponse != null) {
                    val token = loginResponse.data?.token
                    if (token != null) {
                        saveLoginStatus(token)
                        navigateToMainActivity(showScanFragment = true)
                        finish()
                    } else {
                        Toast.makeText(this@Login, "Failed to retrieve token from server", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Toast.makeText(this@Login, "Login failed: ${response.message()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                Toast.makeText(this@Login, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
                Log.e("LoginError", "Error: ${t.message}")
            }
        })
    }

    private fun saveLoginStatus(token: String) {
        val sharedPreferences = getSharedPreferences("auth", MODE_PRIVATE)
        val editor = sharedPreferences.edit()
        editor.putString("token", token) // Simpan token
        editor.putBoolean("isLoggedIn", true) // Tandai user sudah login
        editor.apply()
    }

    private fun isUserLoggedIn(): Boolean {
        val sharedPreferences = getSharedPreferences("auth", MODE_PRIVATE)
        return sharedPreferences.getBoolean("isLoggedIn", false)
    }

    private fun navigateToMainActivity(showScanFragment: Boolean) {
        val intent = Intent(this, MainActivity::class.java)
        intent.putExtra("showScanFragment", showScanFragment)
        startActivity(intent)
    }
}
