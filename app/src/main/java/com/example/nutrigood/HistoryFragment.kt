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
    private lateinit var etBanyakProduk: EditText
    private lateinit var etKategori: EditText
    private lateinit var etRekomendasi: EditText

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val binding = inflater.inflate(R.layout.fragment_history, container, false)

        etProductName = binding.findViewById(R.id.et_product_name)
        etKandungan = binding.findViewById(R.id.et_kandungan)
        etBanyakProduk = binding.findViewById(R.id.et_banyak_produk)
        etKategori = binding.findViewById(R.id.et_kategori)
        etRekomendasi = binding.findViewById(R.id.et_rekomendasi)

        val btnSaveProduct = binding.findViewById<View>(R.id.btn_save_product)
        btnSaveProduct.setOnClickListener {
            saveProduct()
        }

        // Ambil hasil scan dari argumen (jika ada)
        arguments?.getString("scanResult")?.let { scanResult ->
            val sugarValue = extractSugarValue(scanResult)
            val kategori = extractKategori(scanResult)
            val rekomendasi = extractRekomendasi(scanResult)

            if (sugarValue != null) {
                etKandungan.setText(sugarValue.toString())
            } else {
                Toast.makeText(requireContext(), "Tidak ditemukan kandungan gula dalam hasil scan", Toast.LENGTH_SHORT).show()
            }

            etKategori.setText(kategori ?: "Kategori tidak ditemukan")
            etRekomendasi.setText(rekomendasi ?: "Rekomendasi tidak ditemukan")
        }

        return binding
    }

    private fun saveProduct() {
        val productName = etProductName.text.toString().trim()
        val sugarContentText = etKandungan.text.toString().trim()
        val productQuantityText = etBanyakProduk.text.toString().trim()
        val kategori = etKategori.text.toString().trim()
        val rekomendasi = etRekomendasi.text.toString().trim()

        if (productName.isEmpty() || sugarContentText.isEmpty()) {
            Toast.makeText(requireContext(), "Harap lengkapi semua kolom", Toast.LENGTH_SHORT)
                .show()
            return
        }

        val sugarContent = sugarContentText.toDoubleOrNull()
        val productQuantity = productQuantityText.toIntOrNull()

        if (sugarContent == null || productQuantity == null || productQuantity <= 0) {
            Toast.makeText(
                requireContext(),
                "Kandungan gula dan banyak produk harus berupa angka valid",
                Toast.LENGTH_SHORT
            ).show()
            return
        }

        // Hitung total gula
        val totalSugar = sugarContent * productQuantity

        val createdAt =
            java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.getDefault())
                .format(java.util.Date())
        val product = Product(
            namaProduct = productName,
            valueProduct = totalSugar,
            kategori = kategori,
            rekomendasi = rekomendasi,
            createdAt = createdAt
        )

        // Ambil token dari shared preferences
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

            if (token.isNotEmpty()) {
                val apiService = ApiConfig.getApiService()

                // Menyimpan produk biasa terlebih dahulu
                apiService.addProduct("Bearer $token", product).enqueue(object : Callback<Product> {
                    override fun onResponse(call: Call<Product>, response: Response<Product>) {
                        if (response.isSuccessful) {
                            Toast.makeText(
                                requireContext(),
                                "Product saved successfully",
                                Toast.LENGTH_SHORT
                            ).show()

                            // Setelah produk disimpan, simpan produk tersebut sebagai Today's Product
                            apiService.addProductToday("Bearer $token", product)
                                .enqueue(object : Callback<Product> {
                                    override fun onResponse(
                                        call: Call<Product>,
                                        response: Response<Product>
                                    ) {
                                        if (response.isSuccessful) {
                                            Toast.makeText(
                                                requireContext(),
                                                "Today's Product saved successfully",
                                                Toast.LENGTH_SHORT
                                            ).show()
                                        } else {
                                            Toast.makeText(
                                                requireContext(),
                                                "Failed to save today's product: ${response.message()}",
                                                Toast.LENGTH_SHORT
                                            ).show()
                                        }
                                    }

                                    override fun onFailure(call: Call<Product>, t: Throwable) {
                                        Toast.makeText(
                                            requireContext(),
                                            "Network error (Today's Product): ${t.message}",
                                            Toast.LENGTH_SHORT
                                        ).show()
                                    }
                                })

                            // Reset input setelah berhasil
                            etProductName.text.clear()
                            etKandungan.text.clear()
                            etBanyakProduk.text.clear()

                            // Navigasi ke HomeFragment setelah berhasil menyimpan produk
                            val fragmentTransaction =
                                requireActivity().supportFragmentManager.beginTransaction()
                            fragmentTransaction.replace(
                                R.id.fragment_container,
                                HomeFragment()
                            )  // Ganti dengan ID container yang sesuai
                            fragmentTransaction.addToBackStack(null)  // Jika ingin memungkinkan kembali ke HistoryFragment
                            fragmentTransaction.commit()

                        } else {
                            Toast.makeText(
                                requireContext(),
                                "Failed to save product: ${response.message()}",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    }

                    override fun onFailure(call: Call<Product>, t: Throwable) {
                        Toast.makeText(
                            requireContext(),
                            "Network error (Product): ${t.message}",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                })
            } else {
                Toast.makeText(
                    requireContext(),
                    "No token found, please log in",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

        // Fungsi untuk mengekstrak kandungan gula dari hasil scan
    private fun extractSugarValue(input: String): Int? {
        val regexList = listOf(
            "(Total\\s*Sugars|Sugars|Added\\s*Sugars|Sugar|Gula)[:\\-\\s]*(\\d+)\\s*(g|mg)?",
            "(\\d+)\\s*(g|mg)?[:\\-\\s]*(Total\\s*Sugars|Sugars|Added\\s*Sugars|Sugar|Gula)"
        )

        for (regex in regexList) {
            val pattern = regex.toRegex(RegexOption.IGNORE_CASE)
            val matchResult = pattern.find(input)
            if (matchResult != null) {
                val numericValue = matchResult.groups[2]?.value?.toIntOrNull()
                if (numericValue != null) {
                    return numericValue
                }
            }
        }
        return null
    }

    // Fungsi untuk mengekstrak kategori dari hasil scan
    private fun extractKategori(input: String): String? {
        val regex = "(Rendah\\s*gula|Tinggi\\s*gula)".toRegex(RegexOption.IGNORE_CASE)
        return regex.find(input)?.value
    }

    // Fungsi untuk mengekstrak rekomendasi dari hasil scan
    private fun extractRekomendasi(input: String): String? {
        val regex = "(Aman\\s*Dikonsumsi|Kurangi\\s*Konsumsi)".toRegex(RegexOption.IGNORE_CASE)
        return regex.find(input)?.value
    }

