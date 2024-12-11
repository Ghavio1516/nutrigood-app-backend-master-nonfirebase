package com.example.nutrigood

import ProductAdapter
import android.content.Context
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
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
    private lateinit var recyclerViewToday: RecyclerView
    private lateinit var todayProductAdapter: ProductAdapter
    private lateinit var todaysProductText: TextView
    private lateinit var produclistText: TextView

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_home, container, false)

        // Initialize RecyclerView for Product List and Adapter
        recyclerView = view.findViewById(R.id.recycler_view_product_list)
        productAdapter = ProductAdapter { product -> deleteProduct(product) } // Callback for delete
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = productAdapter

        val divider = DividerItemDecoration(requireContext(), DividerItemDecoration.VERTICAL)
        recyclerView.addItemDecoration(divider)

        // Initialize RecyclerView for Today's Product and Adapter
        recyclerViewToday = view.findViewById(R.id.recycler_view_todays_product)
        todayProductAdapter = ProductAdapter { product -> deleteProduct(product) }
        recyclerViewToday.layoutManager = LinearLayoutManager(requireContext())
        recyclerViewToday.adapter = todayProductAdapter

        val dividerToday = DividerItemDecoration(requireContext(), DividerItemDecoration.VERTICAL)
        recyclerViewToday.addItemDecoration(dividerToday)

        // Initialize TextViews
        produclistText = view.findViewById(R.id.product_List)
        todaysProductText = view.findViewById(R.id.todays_product)

        // Set initial visibility (Product List visible, Today's Product hidden)
        recyclerView.visibility = View.VISIBLE
        recyclerViewToday.visibility = View.GONE

        // Fetch the product list and today's product
        fetchProducts()
        fetchTodaysProduct()

        // Set click listener for Product List
        produclistText.setOnClickListener {
            // Show product list, hide today's product
            recyclerView.visibility = View.VISIBLE
            recyclerViewToday.visibility = View.GONE
        }

        // Set click listener for Today's Product
        todaysProductText.setOnClickListener {

            recyclerView.visibility = View.GONE
            recyclerViewToday.visibility = View.VISIBLE
        }

        return view
    }

    // Function to fetch the product list
    private fun fetchProducts() {
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        if (token.isNotEmpty()) {
            val apiService = ApiConfig.getApiService()
            apiService.getProducts("Bearer $token").enqueue(object : Callback<ProductResponse> {
                override fun onResponse(call: Call<ProductResponse>, response: Response<ProductResponse>) {
                    if (response.isSuccessful) {
                        val productResponse = response.body()
                        val products = productResponse?.data?.products // Access data inside `data.products`
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

    // Function to fetch today's product
    private fun fetchTodaysProduct() {
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        if (token.isNotEmpty()) {
            val apiService = ApiConfig.getApiService()

            // Make the API call to fetch today's product
            apiService.getProductToday("Bearer $token").enqueue(object : Callback<Product> {
                override fun onResponse(call: Call<Product>, response: Response<Product>) {
                    if (response.isSuccessful) {
                        val todaysProduct = response.body()

                        if (todaysProduct != null) {
                            todayProductAdapter.setProduct(todaysProduct)
                        } else {
                            Toast.makeText(requireContext(), "No today's product available", Toast.LENGTH_SHORT).show()
                        }
                    } else {
                        Log.e("HomeFragment", "Failed to fetch today's product: ${response.message()}")
                        Toast.makeText(requireContext(), "Failed to fetch today's product", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onFailure(call: Call<Product>, t: Throwable) {
                    Log.e("HomeFragment", "Network error: ${t.message}")
                    Toast.makeText(requireContext(), "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
                }
            })
        } else {
            Toast.makeText(requireContext(), "No token found, please log in", Toast.LENGTH_SHORT).show()
        }
    }


    // Function to handle product deletion
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
                            fetchProducts() // Refresh product list
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
