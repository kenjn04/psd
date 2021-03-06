package com.sample.myapplication

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import androidx.databinding.DataBindingUtil
import androidx.databinding.ObservableField
import com.sample.myapplication.binding.SampleBinding
import com.sample.myapplication.databinding.ActivityMainBinding
import com.sample.myapplication.enums.Test

class MainActivity : AppCompatActivity(), SampleBinding {

    override val name: ObservableField<String> = ObservableField("aaa")
    override val mode: Test = Test.AAA

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val binding: ActivityMainBinding = DataBindingUtil.setContentView(
            this, R.layout.activity_main
        )
        binding.binding = this
    }
}
