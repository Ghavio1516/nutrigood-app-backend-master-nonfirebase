package com.example.nutrigood


import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.example.nutrigood.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.bottomNavigation.backgroundTintList = ColorStateList.valueOf(Color.parseColor("#257180"))

        // Set default fragment
        loadFragment(HomeFragment())

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
            loadFragment(fragment)
            true
        }
    }

    private fun loadFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragment_container, fragment)
            .commit()
    }
}



