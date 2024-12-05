package com.example.nutrigood

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import android.net.Uri
import android.os.Bundle
import android.util.Base64
import android.util.Log
import android.view.View
import android.widget.*
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContentProviderCompat.requireContext
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
import java.io.FileOutputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class ScanFragment : Fragment(R.layout.fragment_scan) {

    private lateinit var cameraExecutor: ExecutorService
    private lateinit var imageView: ImageView
    private lateinit var scanButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var scanResultTextView: TextView // TextView untuk menampilkan hasil scan
    private var isCameraActive = false
    private var cameraProvider: ProcessCameraProvider? = null
    private var capturedPhotoFile: File? = null
    private lateinit var addToHistoryButton: Button


    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        imageView = view.findViewById(R.id.photo_view)
        scanButton = view.findViewById(R.id.btn_scan_button)
        progressBar = view.findViewById(R.id.progress_bar)
        scanResultTextView = view.findViewById(R.id.tv_scan_result)
        addToHistoryButton = view.findViewById(R.id.btn_add_to_history)

        progressBar.visibility = View.GONE
        scanResultTextView.visibility = View.GONE
        scanButton.visibility = View.GONE
        addToHistoryButton.visibility = View.GONE


        addToHistoryButton.setOnClickListener {
            saveToHistory() // Simpan data ke history terlebih dahulu
            navigateToHistoryFragment() // Navigasi ke HistoryFragment
        }


        parentFragmentManager.setFragmentResultListener("photoCaptured", viewLifecycleOwner) { _, bundle ->
            val photoFilePath = bundle.getString("photoFilePath")
            if (photoFilePath != null) {
                val photoFile = File(photoFilePath)
                capturedPhotoFile = photoFile // Save the photo file reference
                displayPhoto(photoFile)
                showPhotoView() // Show the photo in the image view

                // Make the upload button visible after photo is captured
                scanButton.visibility = View.VISIBLE
            }
        }

        val takePhotoButton: Button = view.findViewById(R.id.btn_picture_debug)
        takePhotoButton.text = "Take Photo"
        takePhotoButton.setOnClickListener {
            if (allPermissionsGranted()) {
                openCameraFragment() // Open Camera Fragment
            } else {
                ActivityCompat.requestPermissions(
                    requireActivity(),
                    REQUIRED_PERMISSIONS,
                    CAMERA_REQUEST_CODE
                )
            }
        }


        scanButton.setOnClickListener {
            capturedPhotoFile?.let {
                generateAndUploadBase64(it)
            } ?: Toast.makeText(requireContext(), "No photo to upload", Toast.LENGTH_SHORT).show()
        }

        // Open Gallery Button functionality
        val openGalleryButton: Button = view.findViewById(R.id.btn_open_gallery)
        openGalleryButton.setOnClickListener {
            openGallery()
        }

        cameraExecutor = Executors.newSingleThreadExecutor()
    }

    private fun openCameraFragment() {
        parentFragmentManager.beginTransaction()
            .replace(R.id.fragment_container, CameraFragment())
            .addToBackStack(null)  // Add this to the back stack to allow backward navigation
            .commit()
    }

    private fun openGallery() {
        val intent = Intent(Intent.ACTION_PICK, android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI)
        intent.type = "image/*" // Hanya menampilkan gambar
        startActivityForResult(intent, GALLERY_REQUEST_CODE)
    }

    private fun requestCameraPermission() {
        ActivityCompat.requestPermissions(
            requireActivity(),
            REQUIRED_PERMISSIONS,
            CAMERA_REQUEST_CODE
        )
    }

    private fun stopCamera() {
        cameraProvider?.unbindAll()
        isCameraActive = false
        Log.d(TAG, "Camera stopped")
    }

    private fun fixImageRotation(photoPath: String, bitmap: Bitmap): Bitmap {
        val exifInterface = ExifInterface(photoPath)
        val orientation = exifInterface.getAttributeInt(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_UNDEFINED
        )

        return when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> rotateBitmap(bitmap, 90f)
            ExifInterface.ORIENTATION_ROTATE_180 -> rotateBitmap(bitmap, 180f)
            ExifInterface.ORIENTATION_ROTATE_270 -> rotateBitmap(bitmap, 270f)
            else -> bitmap
        }
    }

    private fun rotateBitmap(bitmap: Bitmap, degrees: Float): Bitmap {
        val matrix = Matrix()
        matrix.postRotate(degrees)
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    private fun displayPhoto(photoFile: File) {
        val options = BitmapFactory.Options().apply { inSampleSize = 4 }
        val bitmap = BitmapFactory.decodeFile(photoFile.absolutePath, options)
        val rotatedBitmap = fixImageRotation(photoFile.absolutePath, bitmap)
        imageView.setImageBitmap(rotatedBitmap)
    }

    private fun showPreviewView() {
        view?.findViewById<PreviewView>(R.id.preview_view)?.visibility = View.VISIBLE
        imageView.visibility = View.GONE
    }

    private fun showPhotoView() {
        view?.findViewById<PreviewView>(R.id.preview_view)?.visibility = View.GONE
        imageView.visibility = View.VISIBLE
    }

    private fun generateAndUploadBase64(file: File) {
        progressBar.visibility = View.VISIBLE // Tampilkan progress bar
        CoroutineScope(Dispatchers.IO).launch {
            try {



                // Baca file yang dikompresi dan ubah ke base64
                val fis = FileInputStream(file)
                val bytes = fis.readBytes()
                fis.close()

                val base64String = "data:image/jpeg;base64," + Base64.encodeToString(bytes, Base64.NO_WRAP)

                // Panggil upload di Main Thread setelah encoding selesai
                withContext(Dispatchers.Main) {
                    uploadPhoto(base64String, "photo_${System.currentTimeMillis()}")
                }
            } catch (e: Exception) {
                Log.e(TAG, "Base64 generation failed", e)

                // Sembunyikan progress bar jika terjadi kesalahan
                withContext(Dispatchers.Main) {
                    progressBar.visibility = View.GONE
                    Toast.makeText(requireContext(), "Error: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }


    private fun uploadPhoto(base64Image: String, fileName: String) {
        progressBar.visibility = View.VISIBLE // ProgressBar tetap aktif saat proses berlangsung

        val sharedPreferences = requireActivity().getSharedPreferences("auth", Context.MODE_PRIVATE)
        val token = sharedPreferences.getString("token", "") ?: ""

        if (token.isEmpty()) {
            progressBar.visibility = View.GONE
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
                // Sembunyikan ProgressBar setelah respons diterima
                progressBar.visibility = View.GONE

                if (response.isSuccessful) {
                    val responseData = response.body()?.data
                    if (responseData != null) {
                        val message = responseData.message
                        val nutritionInfo = responseData.nutrition_info

                        scanResultTextView.visibility = View.VISIBLE
                        scanButton.visibility = View.GONE
                        addToHistoryButton.visibility = View.VISIBLE

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
                    }
                    Toast.makeText(requireContext(), "Photo uploaded successfully", Toast.LENGTH_LONG).show()
                } else {
                    val errorMessage = response.errorBody()?.string() ?: "Unknown error"
                    Log.e(TAG, "Failed to upload photo: $errorMessage")
                    Toast.makeText(requireContext(), "Error: $errorMessage", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<UploadResponse>, t: Throwable) {
                progressBar.visibility = View.GONE // Sembunyikan ProgressBar jika gagal
                Log.e(TAG, "Network error: ${t.message}")
                Toast.makeText(requireContext(), "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(
            requireContext(), it
        ) == PackageManager.PERMISSION_GRANTED
    }
    private fun saveToHistory() {
        val sharedPreferences = requireActivity().getSharedPreferences("history", Context.MODE_PRIVATE)
        val editor = sharedPreferences.edit()

        val currentResult = scanResultTextView.text.toString()

        if (currentResult.isNotEmpty()) {
            // Simpan hasil scan ke dalam daftar history
            val existingHistory = sharedPreferences.getStringSet("historyList", mutableSetOf()) ?: mutableSetOf()
            existingHistory.add(currentResult)
            editor.putStringSet("historyList", existingHistory)
            editor.apply()

            Toast.makeText(requireContext(), "Added to history", Toast.LENGTH_SHORT).show()
            addToHistoryButton.visibility = View.GONE // Sembunyikan tombol setelah ditambahkan ke history
        } else {
            Toast.makeText(requireContext(), "No result to add", Toast.LENGTH_SHORT).show()
        }
    }

    private fun navigateToHistoryFragment() {
        val transaction = parentFragmentManager.beginTransaction()
        val historyFragment = HistoryFragment()

        // Kirim hasil scan sebagai argumen
        val bundle = Bundle()
        val currentResult = scanResultTextView.text.toString()
        bundle.putString("scanResult", currentResult)
        historyFragment.arguments = bundle

        transaction.replace(R.id.fragment_container, historyFragment)
        transaction.addToBackStack(null)
        transaction.commit()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        cameraExecutor.shutdown()
    }

    companion object {
        private const val TAG = "ScanFragment"
        private const val CAMERA_REQUEST_CODE = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
        private const val GALLERY_REQUEST_CODE = 1000
    }
}
