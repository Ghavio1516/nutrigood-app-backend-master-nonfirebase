package com.example.nutrigood

import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.ImageView
import android.widget.Toast
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContentProviderCompat.requireContext
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import java.io.File
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class CameraFragment : Fragment(R.layout.activity_camera) {

    private lateinit var cameraExecutor: ExecutorService
    private lateinit var imageCapture: ImageCapture
    private lateinit var cameraProvider: ProcessCameraProvider
    private var isCameraActive = false
    private var isFrontCamera = false

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val captureImageView: ImageView = view.findViewById(R.id.captureImage)
        val switchCameraImageView: ImageView = view.findViewById(R.id.switchCamera)
        val previewView: PreviewView = view.findViewById(R.id.viewFinder)

        cameraExecutor = Executors.newSingleThreadExecutor()

        // Start the camera when fragment is created
        startCamera(previewView)

        // Capture Image Button
        captureImageView.setOnClickListener {
            captureImage()
        }

        // Switch Camera Button
        switchCameraImageView.setOnClickListener {
            isFrontCamera = !isFrontCamera
            restartCamera(previewView)
        }
    }

    private fun startCamera(previewView: PreviewView) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(requireContext())

        cameraProviderFuture.addListener({
            cameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(previewView.surfaceProvider)
            }

            imageCapture = ImageCapture.Builder().build()

            try {
                cameraProvider.unbindAll()
                val cameraSelector = if (isFrontCamera) CameraSelector.DEFAULT_FRONT_CAMERA else CameraSelector.DEFAULT_BACK_CAMERA
                cameraProvider.bindToLifecycle(
                    viewLifecycleOwner,
                    cameraSelector,
                    preview,
                    imageCapture
                )
                isCameraActive = true
            } catch (exc: Exception) {
                Log.e(TAG, "Camera start failed", exc)
            }
        }, ContextCompat.getMainExecutor(requireContext()))
    }

    private fun restartCamera(previewView: PreviewView) {
        if (isCameraActive) {
            cameraProvider.unbindAll()
            startCamera(previewView)
        }
    }

    private fun captureImage() {
        if (!isCameraActive) {
            Toast.makeText(requireContext(), "Camera is not active", Toast.LENGTH_SHORT).show()
            return
        }

        val photoFile = File(requireContext().externalCacheDir, "${System.currentTimeMillis()}.jpg")
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()

        imageCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(requireContext()),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    Toast.makeText(requireContext(), "Photo saved", Toast.LENGTH_SHORT).show()

                    // Pass the file path back to ScanFragment
                    val bundle = Bundle()
                    bundle.putString("photoFilePath", photoFile.absolutePath)

                    parentFragmentManager.setFragmentResult("photoCaptured", bundle)
                    requireActivity().onBackPressed() // Go back to ScanFragment
                }

                override fun onError(exception: ImageCaptureException) {
                    Log.e(TAG, "Photo capture failed: ${exception.message}", exception)
                }
            }
        )
    }

    override fun onDestroyView() {
        super.onDestroyView()
        cameraExecutor.shutdown()
    }

    companion object {
        private const val TAG = "CameraFragment"
    }
}