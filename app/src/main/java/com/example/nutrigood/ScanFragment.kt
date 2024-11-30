package com.example.nutrigood

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Base64
import android.util.Log
import android.view.View
import android.widget.*
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.data.response.UploadResponse
import com.data.retrofit.ApiConfig
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.io.File
import java.io.FileInputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class ScanFragment : Fragment(R.layout.fragment_scan) {

    private lateinit var cameraExecutor: ExecutorService
    private lateinit var imageView: ImageView
    private lateinit var uploadButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var scanResultTextView: TextView // TextView untuk menampilkan hasil scan
    private var imageCapture: ImageCapture? = null
    private var isCameraActive = false
    private var cameraProvider: ProcessCameraProvider? = null
    private var capturedPhotoFile: File? = null

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        imageView = view.findViewById(R.id.photo_view)
        uploadButton = view.findViewById(R.id.btn_upload_photo)
        progressBar = view.findViewById(R.id.progress_bar)
        scanResultTextView = view.findViewById(R.id.tv_scan_result) // Inisialisasi TextView hasil scan

        progressBar.visibility = View.GONE
        scanResultTextView.visibility = View.GONE // Sembunyikan hasil scan di awal

        val takePhotoButton: Button = view.findViewById(R.id.btn_picture_debug)
        takePhotoButton.text = "Take Photo"
        takePhotoButton.setOnClickListener {
            if (allPermissionsGranted()) {
                takePicture()
            } else {
                ActivityCompat.requestPermissions(
                    requireActivity(),
                    REQUIRED_PERMISSIONS,
                    CAMERA_REQUEST_CODE
                )
            }
        }

        uploadButton.setOnClickListener {
            capturedPhotoFile?.let {
                generateAndUploadBase64(it)
            } ?: Toast.makeText(requireContext(), "No photo to upload", Toast.LENGTH_SHORT).show()
        }

        val toggleCameraButton: Button = view.findViewById(R.id.btn_toggle_camera)
        toggleCameraButton.text = "Turn On Camera"
        toggleCameraButton.setOnClickListener {
            if (isCameraActive) {
                stopCamera()
                toggleCameraButton.text = "Turn On Camera"
            } else {
                if (allPermissionsGranted()) {
                    startCamera()
                    toggleCameraButton.text = "Turn Off Camera"
                } else {
                    ActivityCompat.requestPermissions(
                        requireActivity(),
                        REQUIRED_PERMISSIONS,
                        CAMERA_REQUEST_CODE
                    )
                }
            }
        }

        cameraExecutor = Executors.newSingleThreadExecutor()
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(requireContext())

        cameraProviderFuture.addListener({
            cameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(requireView().findViewById<androidx.camera.view.PreviewView>(R.id.preview_view).surfaceProvider)
            }

            imageCapture = ImageCapture.Builder().build()

            try {
                cameraProvider?.unbindAll()
                cameraProvider?.bindToLifecycle(
                    viewLifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture
                )
                isCameraActive = true
                Log.d(TAG, "Camera started")
            } catch (exc: Exception) {
                Log.e(TAG, "Use case binding failed", exc)
            }
        }, ContextCompat.getMainExecutor(requireContext()))
    }

    private fun stopCamera() {
        cameraProvider?.unbindAll()
        isCameraActive = false
        Log.d(TAG, "Camera stopped")
    }

    private fun takePicture() {
        if (!isCameraActive) {
            Toast.makeText(requireContext(), "Camera is not active", Toast.LENGTH_SHORT).show()
            return
        }

        val photoFile = File(requireContext().externalCacheDir, "${System.currentTimeMillis()}.jpg")
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()

        imageCapture?.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(requireContext()),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    capturedPhotoFile = photoFile
                    Toast.makeText(requireContext(), "Photo Saved", Toast.LENGTH_SHORT).show()
                    displayPhoto(photoFile)
                    uploadButton.visibility = View.VISIBLE
                }

                override fun onError(exception: ImageCaptureException) {
                    Log.e(TAG, "Photo capture failed: ${exception.message}", exception)
                }
            }
        )
    }

    private fun displayPhoto(photoFile: File) {
        val options = BitmapFactory.Options().apply {
            inSampleSize = 4
        }
        val bitmap = BitmapFactory.decodeFile(photoFile.absolutePath, options)
        imageView.setImageBitmap(bitmap)
    }

    private fun generateAndUploadBase64(file: File) {
        progressBar.visibility = View.VISIBLE
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val fis = FileInputStream(file)
                val bytes = fis.readBytes()
                fis.close()

                val base64String = "data:image/jpeg;base64," + Base64.encodeToString(bytes, Base64.NO_WRAP)

                withContext(Dispatchers.Main) {
                    uploadPhoto(base64String, "photo_${System.currentTimeMillis()}")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Base64 generation failed", e)
            } finally {
                withContext(Dispatchers.Main) {
                    progressBar.visibility = View.GONE
                }
            }
        }
    }

    private fun uploadPhoto(base64Image: String, fileName: String) {
        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        if (token.isEmpty()) {
            Toast.makeText(requireContext(), "User not authenticated", Toast.LENGTH_SHORT).show()
            return
        }

        val apiService = ApiConfig.getApiService()
        val payload = mapOf(
            "base64Image" to base64Image,
            "fileName" to fileName
        )

        apiService.uploadPhoto("Bearer $token", payload).enqueue(object : Callback<UploadResponse> {
            override fun onResponse(call: Call<UploadResponse>, response: Response<UploadResponse>) {
                progressBar.visibility = View.GONE
                if (response.isSuccessful) {
                    val responseData = response.body()?.data

                    if (responseData != null) {
                        val message = responseData.message
                        val nutritionInfo = responseData.nutrition_info

                        if (message == "Tidak ditemukan") {
                            scanResultTextView.text = "Hasil Scan: Tidak ditemukan"
                        } else if (nutritionInfo != null && nutritionInfo.isNotEmpty()) {
                            val resultText = nutritionInfo.entries.joinToString(separator = "\n") {
                                "${it.key}: ${it.value}"
                            }
                            scanResultTextView.text = "Hasil Scan:\n$resultText"
                        } else {
                            scanResultTextView.text = "Hasil Scan tidak ditemukan"
                        }
                    } else {
                        scanResultTextView.text = "Hasil Scan tidak ditemukan"
                    }

                    scanResultTextView.visibility = View.VISIBLE
                    uploadButton.visibility = View.GONE
                    Toast.makeText(requireContext(), "Photo uploaded successfully", Toast.LENGTH_LONG).show()
                } else {
                    val errorMessage = response.errorBody()?.string() ?: "Unknown error"
                    Log.e(TAG, "Failed to upload photo: $errorMessage")
                    scanResultTextView.text = "Error: $errorMessage"
                    scanResultTextView.visibility = View.VISIBLE
                    Toast.makeText(requireContext(), "Failed to upload photo: $errorMessage", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<UploadResponse>, t: Throwable) {
                progressBar.visibility = View.GONE
                Log.e(TAG, "Network error: ${t.message}")
                Toast.makeText(requireContext(), "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(requireContext(), it) == PackageManager.PERMISSION_GRANTED
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        stopCamera()
    }

    companion object {
        private const val TAG = "ScanFragment"
        private const val CAMERA_REQUEST_CODE = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }
}
