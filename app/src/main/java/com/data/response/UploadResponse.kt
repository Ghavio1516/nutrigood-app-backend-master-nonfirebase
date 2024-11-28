package com.data.response

data class UploadResponse(
    val status: String,
    val message: String,
    val data: Map<String, String>?
)
