package com.example.nutrigood

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Base64
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import java.io.File
import java.io.FileInputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class ScanFragment : Fragment(R.layout.fragment_scan) {

    private lateinit var cameraExecutor: ExecutorService
    private lateinit var imageView: ImageView
    private lateinit var hashTextView: TextView
    private var imageCapture: ImageCapture? = null
    private var isCameraActive = false // Flag untuk status kamera
    private var cameraProvider: ProcessCameraProvider? = null

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val navigateButton: Button = view.findViewById(R.id.btn_navigate_to_form)
        navigateButton.setOnClickListener {
            parentFragmentManager.beginTransaction()
                .replace(R.id.fragment_container, FormFragment())
                .addToBackStack(null)
                .commit()
        }

        imageView = view.findViewById(R.id.photo_view)
        hashTextView = view.findViewById(R.id.hash_view)

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
                // Gunakan kamera belakang
                cameraProvider?.unbindAll()
                cameraProvider?.bindToLifecycle(
                    viewLifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture
                )
                isCameraActive = true // Kamera aktif
            } catch (exc: Exception) {
                Log.e(TAG, "Use case binding failed", exc)
            }
        }, ContextCompat.getMainExecutor(requireContext()))
    }

    private fun stopCamera() {
        cameraProvider?.unbindAll() // Hentikan semua use case kamera
        isCameraActive = false // Kamera tidak aktif
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
                    Toast.makeText(requireContext(), "Photo Saved", Toast.LENGTH_SHORT).show()
                    displayPhoto(photoFile)
                    generateBase64(photoFile)
                }

                override fun onError(exception: ImageCaptureException) {
                    Log.e(TAG, "Photo capture failed: ${exception.message}", exception)
                }
            }
        )
    }

    private fun displayPhoto(photoFile: File) {
        val bitmap = BitmapFactory.decodeFile(photoFile.absolutePath)
        imageView.setImageBitmap(bitmap)
    }

    private fun generateBase64(file: File) {
        try {
            val fis = FileInputStream(file)
            val bytes = fis.readBytes() // Baca semua byte dari file
            fis.close()

            // Konversi byte array ke string Base64
            val base64String = Base64.encodeToString(bytes, Base64.DEFAULT)
            hashTextView.text = "Base64: $base64String"
            Log.d(TAG, "Base64 Hash: $base64String")
        } catch (e: Exception) {
            Log.e(TAG, "Base64 generation failed", e)
        }
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
