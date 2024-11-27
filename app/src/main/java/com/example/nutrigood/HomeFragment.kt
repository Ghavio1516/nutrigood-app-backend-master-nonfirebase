package com.example.nutrigood

import android.content.Context
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.DividerItemDecoration
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.data.retrofit.ApiConfig
import com.data.response.Product
import com.data.response.ProductResponse
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class HomeFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var productAdapter: ProductAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_home, container, false)

        // Inisialisasi RecyclerView dan Adapter
        recyclerView = view.findViewById(R.id.recycler_view)
        productAdapter = ProductAdapter { product -> deleteProduct(product) } // Callback untuk delete
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = productAdapter

        val divider = DividerItemDecoration(requireContext(), DividerItemDecoration.VERTICAL)
        recyclerView.addItemDecoration(divider)


        // Fetch products dari backend
        fetchProducts()

        return view
    }

    private fun fetchProducts() {
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        if (token.isNotEmpty()) {
            val apiService = ApiConfig.getApiService()
            apiService.getProducts("Bearer $token").enqueue(object : Callback<ProductResponse> {
                override fun onResponse(call: Call<ProductResponse>, response: Response<ProductResponse>) {
                    if (response.isSuccessful) {
                        val productResponse = response.body()
                        val products = productResponse?.data?.products // Akses data di dalam `data.products`
                        if (products != null && products.isNotEmpty()) {
                            productAdapter.setProducts(products)
                        } else {
                            Toast.makeText(
                                requireContext(),
                                "No products available",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    } else {
                        Log.e("HomeFragment", "Failed to fetch products: ${response.message()}")
                        Toast.makeText(
                            requireContext(),
                            "Failed to fetch products",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }


                override fun onFailure(call: Call<ProductResponse>, t: Throwable) {
                    Log.e("HomeFragment", "Network error: ${t.message}")
                    Toast.makeText(
                        requireContext(),
                        "Network error: ${t.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            })
        } else {
            Toast.makeText(requireContext(), "No token found, please log in", Toast.LENGTH_SHORT).show()
        }
    }

    private fun deleteProduct(product: Product) {
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        if (token.isNotEmpty()) {
            val apiService = ApiConfig.getApiService()
            val productId = product.id
            if (productId != null) {
                apiService.deleteProduct("Bearer $token", productId).enqueue(object : Callback<Void> {
                    override fun onResponse(call: Call<Void>, response: Response<Void>) {
                        Log.d("HomeFragment", "Delete Response Code: ${response.code()}")

                        if (response.isSuccessful) {
                            Toast.makeText(requireContext(), "Product deleted successfully", Toast.LENGTH_SHORT).show()
                            fetchProducts() // Refresh daftar produk
                        } else {
                            Log.e("HomeFragment", "Failed to delete product: ${response.message()}")
                            Toast.makeText(requireContext(), "Failed to delete product", Toast.LENGTH_SHORT).show()
                        }
                    }

                    override fun onFailure(call: Call<Void>, t: Throwable) {
                        Log.e("HomeFragment", "Network error: ${t.message}")
                        Toast.makeText(requireContext(), "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                })
            } else {
                Toast.makeText(requireContext(), "Product ID is missing", Toast.LENGTH_SHORT).show()
            }
        } else {
            Toast.makeText(requireContext(), "No token found, please log in", Toast.LENGTH_SHORT).show()
        }
    }
}
