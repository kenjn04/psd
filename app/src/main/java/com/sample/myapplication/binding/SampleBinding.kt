package com.sample.myapplication.binding

import androidx.databinding.ObservableField
import com.sample.myapplication.enum.Test

interface SampleBinding {

    val name: ObservableField<String>
    val mode: Test

}