package com.data.response

data class Product(
    val id: Int? = null,
    val userId: String? = null,
    val namaProduct: String,
    val valueProduct: Double,
    val kategori: String?,
    val rekomendasi: String?,
    val createdAt: String? = null
)