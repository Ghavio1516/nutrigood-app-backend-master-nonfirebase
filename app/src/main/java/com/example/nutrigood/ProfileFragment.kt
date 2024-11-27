package com.example.nutrigood

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.data.retrofit.ApiConfig
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import com.data.response.UserDetailsResponse

class ProfileFragment : Fragment() {

    private lateinit var mUserEmail: TextView
    private lateinit var mUserName: TextView
    private lateinit var mLogoutButton: Button

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        // Inflate the fragment layout
        val view = inflater.inflate(R.layout.fragment_profile, container, false)

        // Initialize UI elements
        mUserEmail = view.findViewById(R.id.tv_user_email)
        mUserName = view.findViewById(R.id.tv_user_name)
        mLogoutButton = view.findViewById(R.id.btn_logout)

        // Fetch user data
        fetchUserData()

        // Set up Logout button functionality
        mLogoutButton.setOnClickListener {
            logoutUser()
        }

        return view
    }

    // Fetch the user data from SharedPreferences and backend API
    private fun fetchUserData() {
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        if (token.isNotEmpty()) {
            Log.d("ProfileFragment", "Token: $token")

            val apiService = ApiConfig.getApiService()
            apiService.getUserDetails("Bearer $token").enqueue(object : Callback<UserDetailsResponse> {
                override fun onResponse(call: Call<UserDetailsResponse>, response: Response<UserDetailsResponse>) {
                    Log.d("ProfileFragment", "Response Code: ${response.code()}")
                    Log.d("ProfileFragment", "Raw JSON Body: ${response.errorBody()?.string() ?: response.body()}") // Tambahkan log untuk JSON mentah

                    if (response.isSuccessful) {
                        val userDetails = response.body()
                        Log.d("ProfileFragment", "Parsed Response: $userDetails") // Log hasil parsing
                        if (userDetails != null) {
                            mUserEmail.text = userDetails.email
                            mUserName.text = userDetails.username
                        }
                    } else {
                        Log.e("ProfileFragment", "Failed to fetch user details: ${response.message()}")
                        Toast.makeText(requireContext(), "Failed to fetch user details", Toast.LENGTH_SHORT).show()
                    }
                }


                override fun onFailure(call: Call<UserDetailsResponse>, t: Throwable) {
                    Log.e("ProfileFragment", "Network error: ${t.message}")
                    Toast.makeText(requireContext(), "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            })
        } else {
            Toast.makeText(requireContext(), "No token found, please log in", Toast.LENGTH_SHORT).show()
            logoutUser()
        }
    }


    // Logout the user
    private fun logoutUser() {
        // Clear token from SharedPreferences
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val editor = sharedPreferences.edit()
        editor.clear()
        editor.apply()

        Toast.makeText(context, "Logged out successfully", Toast.LENGTH_SHORT).show()

        val intent = Intent(activity, Login::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
    }
}
