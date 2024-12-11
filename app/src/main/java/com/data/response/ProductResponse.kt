package com.data.response

data class ProductResponse(
    val data: ProductData
)

data class ProductData(
    val products: List<Product>
)