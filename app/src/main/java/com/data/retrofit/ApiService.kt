package com.data.retrofit

import com.data.response.LoginRequest
import com.data.response.LoginResponse
import com.data.response.Product
import com.data.response.ProductResponse
import com.data.response.User
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import com.data.response.UserDetailsResponse
import retrofit2.http.DELETE

interface ApiService {
    // Endpoint untuk registrasi pengguna
    @POST("users/register")
    fun registerUser(@Body user: User): Call<Void>

    // Endpoint untuk login pengguna
    @POST("users/login")
    fun loginUser(@Body loginRequest: LoginRequest): Call<LoginResponse>

    @GET("users/details")
    fun getUserDetails(@Header("Authorization") token: String): Call<UserDetailsResponse>


    // Endpoint untuk menambahkan produk (autentikasi diperlukan)
    @POST("products")
    fun addProduct(
        @Header("Authorization") token: String, // Menyisipkan token JWT di header
        @Body product: Product
    ): Call<Product>

    // Endpoint untuk mendapatkan detail produk (autentikasi diperlukan)
    @GET("products/{id}")
    fun getProduct(
        @Header("Authorization") token: String, // Menyisipkan token JWT di header
        @Path("id") id: Int
    ): Call<Product>

    @GET("products")
    fun getProducts(
        @Header("Authorization") token: String
    ): Call<ProductResponse>

    @DELETE("products/{id}")
    fun deleteProduct(
        @Header("Authorization") token: String,
        @Path("id") id: Int
    ): Call<Void>

}
