package com.example.nutrigood

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ImageButton
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.data.response.Product

class ProductAdapter(
    private val onDeleteClick: (Product) -> Unit // Callback untuk tombol Delete
) : RecyclerView.Adapter<ProductAdapter.ProductViewHolder>() {

    private val productList = mutableListOf<Product>()

    fun setProducts(products: List<Product>) {
        productList.clear()
        productList.addAll(products)
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProductViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_product, parent, false)
        return ProductViewHolder(view)
    }

    override fun onBindViewHolder(holder: ProductViewHolder, position: Int) {
        val product = productList[position]
        holder.bind(product)
    }

    override fun getItemCount(): Int = productList.size

    inner class ProductViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvName: TextView = itemView.findViewById(R.id.tv_product_name)
        private val tvSugarContent: TextView = itemView.findViewById(R.id.tv_sugar_content)
        private val btnDelete: ImageButton = itemView.findViewById(R.id.btn_delete)

        fun bind(product: Product) {
            tvName.text = product.namaProduct
            tvSugarContent.text = "Sugar: ${product.valueProduct} g"

            // Handle tombol Delete
            btnDelete.setOnClickListener {
                onDeleteClick(product)
            }
        }
    }
}
