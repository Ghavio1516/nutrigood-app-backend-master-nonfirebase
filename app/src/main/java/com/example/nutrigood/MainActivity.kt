package com.example.nutrigood

import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Bundle
import android.os.Looper
import android.util.Log
import android.view.View
import android.os.Handler
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import androidx.fragment.app.FragmentTransaction
import com.example.nutrigood.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.bottomNavigation.backgroundTintList =
            ColorStateList.valueOf(Color.parseColor("#257180"))

        // Check if need to show ScanFragment
        if (intent.getBooleanExtra("showScanFragment", false)) {
            loadFragmentWithProgress(ScanFragment())
            binding.bottomNavigation.selectedItemId = R.id.nav_scan
        } else {
            // Set default fragment
            loadFragmentWithProgress(HomeFragment())
        }

        // BottomNavigationView item selected listener
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            val fragment: Fragment = when (item.itemId) {
                R.id.nav_home -> {
                    Log.d("BottomNav", "Home selected")
                    HomeFragment()
                }

                R.id.nav_scan -> {
                    Log.d("BottomNav", "Scan selected")
                    ScanFragment()
                }

                R.id.nav_profile -> {
                    Log.d("BottomNav", "Profile selected")
                    ProfileFragment()
                }

                else -> HomeFragment()
            }
            loadFragmentWithProgress(fragment)
            true
        }
    }

    private fun loadFragmentWithProgress(fragment: Fragment, processDuration: Long = 0L) {
        // Tampilkan ProgressBar
        binding.progressBar.visibility = View.VISIBLE

        supportFragmentManager.beginTransaction()
            .setTransition(FragmentTransaction.TRANSIT_FRAGMENT_FADE)
            .replace(R.id.fragment_container, fragment)
            .runOnCommit {
                if (processDuration > 0L) {
                    // Jika ada durasi proses tambahan, tunggu hingga selesai
                    Handler(Looper.getMainLooper()).postDelayed({
                        binding.progressBar.visibility = View.GONE
                    }, processDuration)
                } else {
                    // Sembunyikan ProgressBar segera setelah fragment selesai dimuat
                    binding.progressBar.visibility = View.GONE
                }
            }
            .commit()
    }
}
