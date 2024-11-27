package com.data.response

import com.google.gson.annotations.SerializedName

data class UserDetailsResponse(
    @SerializedName("username") val username: String?,
    @SerializedName("email") val email: String?
)
