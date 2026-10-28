package com.popcap.SexyAppFramework.utils;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class Inventory {
    Map<String, SkuDetails> mSkuMap = new HashMap();
    Map<String, Purchase> mPurchaseMap = new HashMap();

    Inventory() {
    }

    public SkuDetails getSkuDetails(String sku) {
        return this.mSkuMap.get(sku);
    }

    public Purchase getPurchase(String sku) {
        return this.mPurchaseMap.get(sku);
    }

    public boolean hasPurchase(String sku) {
        return this.mPurchaseMap.containsKey(sku);
    }

    public boolean hasDetails(String sku) {
        return this.mSkuMap.containsKey(sku);
    }

    public Collection<SkuDetails> getAllSkuDetails() {
        return this.mSkuMap.values();
    }

    public List<Purchase> getAllPurchases() {
        return new ArrayList(this.mPurchaseMap.values());
    }

    public void erasePurchase(String sku) {
        if (this.mPurchaseMap.containsKey(sku)) {
            this.mPurchaseMap.remove(sku);
        }
    }

    List<String> getAllOwnedSkus() {
        return new ArrayList(this.mPurchaseMap.keySet());
    }

    void addSkuDetails(SkuDetails d) {
        this.mSkuMap.put(d.getSku(), d);
    }

    void addPurchase(Purchase p) {
        this.mPurchaseMap.put(p.getSku(), p);
    }
}
