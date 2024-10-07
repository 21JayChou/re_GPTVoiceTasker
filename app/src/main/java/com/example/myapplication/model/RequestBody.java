package com.example.myapplication.model;

public class RequestBody {
    String model = "gpt-3.5-turbo";

    String prompt;
    double temperature = 0.5;
    int max_tokens = 200;

    public RequestBody(String prompt) {
        this.prompt = prompt;
    }
}
