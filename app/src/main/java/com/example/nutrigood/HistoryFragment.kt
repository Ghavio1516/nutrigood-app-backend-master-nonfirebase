package com.example.nutrigood

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.data.response.Product
import com.data.retrofit.ApiConfig
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class HistoryFragment : Fragment() {

    private lateinit var etProductName: EditText
    private lateinit var etKandungan: EditText

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val binding = inflater.inflate(R.layout.fragment_history, container, false)

        etProductName = binding.findViewById(R.id.et_product_name)
        etKandungan = binding.findViewById(R.id.et_kandungan)

        val btnSaveProduct = binding.findViewById<View>(R.id.btn_save_product)
        btnSaveProduct.setOnClickListener {
            saveProduct()
        }

        // Ambil hasil scan dari argumen (jika ada)
        arguments?.getString("scanResult")?.let { scanResult ->
            val sugarValue = extractSugarValue(scanResult)
            if (sugarValue != null) {
                etKandungan.setText(sugarValue.toString())
            } else {
                Toast.makeText(requireContext(), "Tidak ditemukan kandungan gula dalam hasil scan", Toast.LENGTH_SHORT).show()
            }
        }

        return binding
    }

    private fun saveProduct() {
        val productName = etProductName.text.toString().trim()
        val sugarContentText = etKandungan.text.toString().trim()

        if (productName.isEmpty() || sugarContentText.isEmpty()) {
            Toast.makeText(requireContext(), "Harap lengkapi semua kolom", Toast.LENGTH_SHORT).show()
            return
        }

        val sugarContent = sugarContentText.toDoubleOrNull()
        if (sugarContent == null) {
            Toast.makeText(requireContext(), "Kandungan gula harus berupa angka", Toast.LENGTH_SHORT).show()
            return
        }

        // Ambil waktu sekarang sebagai createdAt
        val createdAt = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.getDefault()).format(java.util.Date())

        // Buat objek Product
        val product = Product(namaProduct = productName, valueProduct = sugarContent, createdAt = createdAt)

        // Ambil token dari shared preferences
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        val apiService = ApiConfig.getApiService()
        apiService.addProduct("Bearer $token", product).enqueue(object : Callback<Product> {
            override fun onResponse(call: Call<Product>, response: Response<Product>) {
                if (response.isSuccessful) {
                    Toast.makeText(requireContext(), "Product saved successfully", Toast.LENGTH_SHORT).show()
                    // Reset input setelah berhasil
                    etProductName.text.clear()
                    etKandungan.text.clear()
                } else {
                    Toast.makeText(requireContext(), "Failed to save product: ${response.message()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<Product>, t: Throwable) {
                Toast.makeText(requireContext(), "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    // Fungsi untuk mengekstrak kandungan gula dari hasil scan
    private fun extractSugarValue(input: String): Int? {
        // Daftar pola regex untuk mencocokkan berbagai format kandungan gula
        val regexList = listOf(
            "(Total\\s*Sugars|Sugars|Added\\s*Sugars|Sugar|Gula)[:\\-\\s]*(\\d+)\\s*(g|mg|9)?", // Pola 1: Teks gula diikuti angka
            "(\\d+)\\s*(g|mg|9)?[:\\-\\s]*(Total\\s*Sugars|Sugars|Added\\s*Sugars|Sugar|Gula)"  // Pola 2: Angka diikuti teks gula
        )

        for (regex in regexList) {
            val pattern = regex.toRegex(RegexOption.IGNORE_CASE) // Abaikan case
            val matchResult = pattern.find(input)
            if (matchResult != null) {
                // Coba konversi angka yang ditemukan menjadi integer
                val numericValue = matchResult.groups[2]?.value?.toIntOrNull()
                if (numericValue != null) {
                    return numericValue
                }
            }
        }
        return null // Jika tidak ditemukan angka yang valid
    }
    }
