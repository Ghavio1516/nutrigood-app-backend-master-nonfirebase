package com.data.response

data class UploadResponse(
    val status: String,
    val message: String,
    val data: Data?
) {
    data class Data(
        val message: String,
        val nutrition_info: Map<String, String>?
    )
}
