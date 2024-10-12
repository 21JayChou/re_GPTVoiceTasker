package com.example.myapplication;

import org.junit.Test;

import static org.junit.Assert.*;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Example local unit test, which will execute on the development machine (host).
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
public class ExampleUnitTest {
    private static final String DATA_DIR = "C:/Users/25061/Desktop/data";
    private Map<List<String>,Boolean>data;
    private List<Boolean>flags;
    public static String readFile2String(String path) throws IOException {
        return new String(Files.readAllBytes(Paths.get(path)));
    }

    public static double calculateStringSimilarity(String path1, String path2) throws IOException {
        String str1 = readFile2String(path1);
        String str2 = readFile2String(path2);
        str1 = str1.replaceAll(" id=\"[0-9]+\"", "");
        str2 = str2.replaceAll(" id=\"[0-9]+\"", "");
        int len1 = str1.length();
        int len2 = str2.length();
//        int[][] distance = new int[len1 + 1][len2 + 1];
//
//        for (int i = 0; i <= len1; i++) {
//            distance[i][0] = i;
//        }
//        for (int j = 0; j <= len2; j++) {
//            distance[0][j] = j;
//        }
//
//        for (int i = 1; i <= len1; i++) {
//            for (int j = 1; j <= len2; j++) {
//                int cost = (str1.charAt(i - 1) == str2.charAt(j - 1)) ? 0 : 1;
//                distance[i][j] = Math.min(Math.min(distance[i - 1][j] + 1, distance[i][j - 1] + 1), distance[i - 1][j - 1] + cost);
//            }
//        }
        // 使用两个数组交替存储当前行和前一行
        int[] prev = new int[len2 + 1];
        int[] curr = new int[len2 + 1];

        // 初始化 prev 行
        for (int j = 0; j <= len2; j++) {
            prev[j] = j;
        }

        for (int i = 1; i <= len1; i++) {
            curr[0] = i;  // 当前行的第一个元素
            for (int j = 1; j <= len2; j++) {
                int cost = (str1.charAt(i - 1) == str2.charAt(j - 1)) ? 0 : 1;
                curr[j] = Math.min(Math.min(curr[j - 1] + 1, prev[j] + 1), prev[j - 1] + cost);
            }
            // 将当前行变为前一行，准备计算下一行
            int[] temp = prev;
            prev = curr;
            curr = temp;
        }

        // double sim = 1.0 - ((double) distance[len1][len2] / Math.max(len1, len2));
        double sim = 1.0 - ((double) prev[len2] / Math.max(len1, len2));  // 注意这里使用的是 prev，因为最后一次交换后，prev 存储了最终的结果


        return sim ;
    }

    public static String calculatepHash(String path) {
        Bitmap image = BitmapFactory.decodeFile(path);

        // 1. 将图像缩小到8x8
        Bitmap resizedImage = Bitmap.createScaledBitmap(image, 8, 8, false);

        // 2. 转换为灰度图像
        Bitmap grayImage = toGrayscale(resizedImage);

        // 3. 计算DCT
        int[] dctCoefficients = dct(grayImage);

        // 4. 计算平均值
        int average = calculateAverage(dctCoefficients);

        // 5. 生成哈希值
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 8 * 8; i++) {
            int pixel = dctCoefficients[i];
            sb.append((pixel > average) ? "1" : "0");
        }

        return sb.toString();
    }

    private static Bitmap toGrayscale(Bitmap image) {
        int width = image.getWidth();
        int height = image.getHeight();
        int[] pixels = new int[width * height];
        image.getPixels(pixels, 0, width, 0, 0, width, height);

        for (int i = 0; i < pixels.length; i++) {
            int gray = (int) (Color.red(pixels[i]) * 0.3 + Color.green(pixels[i]) * 0.59 + Color.blue(pixels[i]) * 0.11);
            pixels[i] = gray | (gray << 8) | (gray << 16) | 0xFF000000;
        }

        Bitmap grayscaleBitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        grayscaleBitmap.setPixels(pixels, 0, width, 0, 0, width, height);
        return grayscaleBitmap;
    }

    private static int[] dct(Bitmap image) {
        int width = image.getWidth();
        int height = image.getHeight();
        int[] pixels = new int[width * height];
        image.getPixels(pixels, 0, width, 0, 0, width, height);

        int[] dct = new int[width * height];
        for (int x = 0; x < width; x++) {
            for (int y = 0; y < height; y++) {
                double sum = 0.0;
                for (int i = 0; i < width; i++) {
                    for (int j = 0; j < height; j++) {
                        double cosx = (x == 0) ? 1.0 / Math.sqrt(width) : Math.cos((2 * i + 1) * x * Math.PI / (2 * width));
                        double cosy = (y == 0) ? 1.0 / Math.sqrt(height) : Math.cos((2 * j + 1) * y * Math.PI / (2 * height));
                        sum += pixels[i * height + j] * cosx * cosy;
                    }
                }
                dct[x * height + y] = (int) sum;
            }
        }
        return dct;
    }

    private static int calculateAverage(int[] dctCoefficients) {
        int sum = 0;
        for (int coeff : dctCoefficients) {
            sum += coeff;
        }
        return sum / (8 * 8);
    }

    public static int hammingDistance(String s1, String s2) {
        int distance = 0;
        for (int i = 0; i < s1.length(); i++) {
            if (s1.charAt(i) != s2.charAt(i)) {
                distance++;
            }
        }
        return distance;
    }

    public static double calculatePHashSimilarity( String path1, String path2){
        String pHash1 = calculatepHash(path1), pHash2 = calculatepHash(path2);
        return 1- hammingDistance(pHash1, pHash2)*1.0/64;
    }

    public static double calculateCombinedSimilarity(String xmlPath1, String imgPath1, String xmlPath2, String imgPath2) throws IOException {
        double pHashSimilarity = calculatePHashSimilarity(imgPath1, imgPath2);
        double xmlSimilarity = calculateStringSimilarity(xmlPath1, xmlPath2);


        return (pHashSimilarity + xmlSimilarity)/2;
    }

    public ExampleUnitTest() {
        flags = new ArrayList<>();
        data = new HashMap<>();
        flags.add(true);
        flags.add(true);
        flags.add(false);
        flags.add(true);
        flags.add(true);
        flags.add(false);
        flags.add(false);
        flags.add(false);
        flags.add(false);
        flags.add(false);
        flags.add(true);
        flags.add(false);
        flags.add(true);
        flags.add(true);
        flags.add(false);
        for (int i = 0; i < 15; i++) {
            List<String>paths = new ArrayList<>();
            paths.add(DATA_DIR+"/screenshots/"+(i*2+1)+".jpg");
            paths.add(DATA_DIR+"/screenshots/"+(i*2+2)+".jpg");
            paths.add(DATA_DIR+"/xmls/"+(i*2+1)+".xml");
            paths.add(DATA_DIR+"/xmls/"+(i*2+2)+".xml");
            data.put(paths, flags.get(i));
        }
    }
    public void testResult(int tp, int tn, int fp, int fn){
        System.out.println("Accuracy:"+(tp+tn)*1.0/(tp+tn+fp+fn));
        System.out.println("Precision:"+tp*1.0/(tp+fp));
        System.out.println("Recall:"+tp*1.0/(tp+fn));
    }
    @Test
    public void testStringSimilarity() throws IOException {
        int tp=0,tn=0,fp=0,fn=0;
        for(List<String>paths:data.keySet()){
            boolean predict = calculateStringSimilarity(paths.get(2), paths.get(3))>0.7;
            boolean flag = data.get(paths);
            if(flag && predict) tp++;
            else if(flag && !predict)fn++;
            else if(!flag && predict)fp++;
            else tn++;
        }
        testResult(tp,tn,fp,fn);
    }

    @Test
    public void testpHashSimilarity() throws IOException {
        int tp=0,tn=0,fp=0,fn=0;
        for(List<String>paths:data.keySet()){
            boolean predict = calculatePHashSimilarity(paths.get(0), paths.get(1))>0.7;
            boolean flag = data.get(paths);
            if(flag && predict) tp++;
            else if(flag && !predict)fn++;
            else if(!flag && predict)fp++;
            else tn++;
        }
        testResult(tp,tn,fp,fn);
    }

    @Test
    public void testCombinedSimilarity() throws IOException {
        int tp=0,tn=0,fp=0,fn=0;
        for(List<String>paths:data.keySet()){
            boolean predict = calculateCombinedSimilarity(paths.get(2), paths.get(0), paths.get(3), paths.get(1))>0.7;
            boolean flag = data.get(paths);
            if(flag && predict) tp++;
            else if(flag && !predict)fn++;
            else if(!flag && predict)fp++;
            else tn++;
        }
        testResult(tp,tn,fp,fn);
    }

}