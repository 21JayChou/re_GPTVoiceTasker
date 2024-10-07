package com.example.myapplication;

import com.example.myapplication.model.ChatRequestBody;
import com.example.myapplication.model.ChatResponseObject;
import com.example.myapplication.model.RequestBody;
import com.example.myapplication.model.ResponseObject;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.Headers;
import retrofit2.http.POST;

public interface JsonApi {


    @Headers({"Content-Type: application/json", "Authorization: Bearerxxx"})
    @POST("v1/chat/completions")
    Call<ResponseObject> getData(@Body RequestBody requestBody);

    @Headers({"Content-Type: application/json", "Authorization: Bearerxxx"})
    @POST("v1/chat/completions")
    Call<ChatResponseObject> getDataChat(@Body ChatRequestBody requestBody);


}
