package com.data.retrofit

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiConfig {
    fun getApiService(): ApiService {
        val client = OkHttpClient.Builder()
            .connectTimeout(120, TimeUnit.SECONDS) // Timeout untuk koneksi
            .readTimeout(120, TimeUnit.SECONDS)  // Timeout untuk membaca data
            .writeTimeout(120, TimeUnit.SECONDS) // Timeout untuk menulis data
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl("https://nutrigood.akmalnurwahid.my.id") // URL backend
            .addConverterFactory(GsonConverterFactory.create())
            .client(client)
            .build()

        return retrofit.create(ApiService::class.java)
    }
}
