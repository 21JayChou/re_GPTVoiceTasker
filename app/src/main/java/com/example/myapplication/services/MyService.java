package com.example.myapplication.services;

import static androidx.core.app.ActivityCompat.startActivityForResult;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.speech.SpeechRecognizer;
import android.text.TextUtils;
import android.util.DisplayMetrics;
import android.util.Log;
import android.util.Xml;
import android.view.Display;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.Button;
import android.widget.FrameLayout;

import androidx.annotation.NonNull;
import androidx.constraintlayout.utils.widget.MotionLabel;

import com.example.myapplication.R;
import com.example.myapplication.graphdatabase.Graph;
import com.example.myapplication.graphdatabase.Node;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import com.example.myapplication.Command;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;
import com.example.myapplication.JsonApi;
import com.example.myapplication.model.ChatRequestBody;
import com.example.myapplication.model.ChatResponseObject;
import com.example.myapplication.model.LabelFoundNode;
import com.example.myapplication.model.PackageDataObject;
import com.example.myapplication.model.RequestBody;
import com.example.myapplication.model.ResponseObject;
import com.example.myapplication.graphdatabase.Utils;
import com.example.myapplication.graphdatabase.Edge;
import com.example.myapplication.AccessibilityNodeInfoDumper;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;

import org.xmlpull.v1.XmlSerializer;


public class MyService extends AccessibilityService implements View.OnTouchListener{

    final String FILE_NAME = "voicify";
    int width, height;
    Button startButton;
    Button dumpBtn;

    Retrofit retrofit;
    String currentActivityName;
    JsonApi jsonApi;
    //ChatHistory chatHistory;
    ArrayList<String> uiElements = new ArrayList<String>();
    ArrayList<String> appNames = new ArrayList<String>();
    SharedPreferences mPrefs;

    AccessibilityNodeInfo currentSource;
    AccessibilityNodeInfo previousSource;
    ArrayList<AccessibilityNodeInfo> scrollableNodes = new ArrayList<AccessibilityNodeInfo>();
    String componentAsString = "";
    FrameLayout mLayout;
    ArrayList<LabelFoundNode> foundLabeledNodes = new ArrayList<>();
    //ArrayList<TooltipRequiredNode> tooltipRequiredNodes = new ArrayList<>();

    boolean isVoiceCommandConnected = false;
    String currentCommand = "";
    int noOfLabels = 0;
    SpeechRecognizer speechRecognizer;                      // declaring speech recognition var
    Intent speechRecognizerIntent;
    String debugLogTag = "FIT4003_VOICIFY";                  // use this tag for all log tags.
    ArrayList<String> launchTriggers = new ArrayList<String>(Arrays.asList("load", "launch", "execute", "open"));

    // Defining window manager for overlay elements and switchBar
    WindowManager wm;
    WindowManager.LayoutParams switchBar; // stores layout parameters for movable switchBar

    long currentTime;

    // variable for switch bar coordinates
    private int initialX;
    private int initialY;
    private float initialTouchX;
    private float initialTouchY;

    private int currentTooltipCount = 1;

    Graph graph;
    String currentPackageName = "";
    Node currentNodeGraph;
    boolean isExecuting = false;

    // new code
    //ArrayList<PackageDataObject> packageDataObjects = new ArrayList<>();
    int currentIntentIndex = 0;
    String currentOpeningPackage;
    String currentOpeningFeature;
    String currentAppName;

    ArrayList<String> matchedIntents = new ArrayList<>();

    String[] tooltipColorSpinnerItems = new String[]{"#64b5f6", "#2b2b2b", "#ff4040"};
    int[] tooltipSizeSpinnerItems = new int[]{14, 18, 22};
    int[] tooltipOpacitySpinnerItems = new int[]{250, 220, 170, 120};

    int tooltipColor = 0;
    int tooltipSize = 0;
    int tooltipOpacity = 0;

    String previousEventCode = "";

    String currentScreenXML = "";
    ArrayList<PackageDataObject> packageDataObjects = new ArrayList<>();
    MotionLabel textMsg = null;
    private boolean isStarted;
    AccessibilityServiceInfo serviceInfo;

    private void updateScreenXML() {
        XmlSerializer serializer = Xml.newSerializer();
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        try {
            serializer.setOutput(outputStream, "UTF-8");
            serializer.startDocument(null, true);
            AccessibilityNodeInfoDumper.dumpNodeRec(getRootInActiveWindow(), serializer, 0, false, width, height, false);
            serializer.endDocument();
            currentScreenXML = outputStream.toString("UTF-8");

            Log.d("CURRENT SCREEN XML", currentScreenXML);

        } catch (IOException e) {
            e.printStackTrace();
        }
    }



    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (!isStarted) return;
        AccessibilityNodeInfo source = event.getSource();
        setCurrentActName(event);
        //Log.d("DEBUG","1");
        if ((source == null) || (previousEventCode.equals("32") && previousSource!= null && event.getEventType() == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED)
        ) {

            return;
        }
        if ((previousSource!= null && (previousSource.hashCode() == source.hashCode() || previousSource.equals(source))) && !currentCommand.equals("")) {
            Log.d("GG", "confirmed");
        }

        previousSource = source;
        previousEventCode = event.getEventType() + "";
        String actionDescription = getActionDescription(event.getEventType());
        Log.d("EventType", event.getEventType()+"");
        Log.d("Action", actionDescription == null?"":actionDescription);
//        if (isNotBlockedEvent()) {
//            currentSource = getRootInActiveWindow(); // update the current root node
//            updateScreenXML();
//        }
        currentSource = getRootInActiveWindow(); // update the current root node
        updateScreenXML();
        Rect rect = new Rect();
        if("View Clicked".equals(actionDescription)){
            source.getBoundsInScreen(rect);
            updateGraphDB(source.toString(), "Press",rect.toShortString() );
        }

    }

    @Override
    public void onInterrupt() {

    }


    protected void onServiceConnected() {
        /**
         * This function is invoked after the accessibility service has been stared by the user. this
         * function inflates the layout and draws the floating UI for the service. It also initialises
         * speech recognition & checks audio permissions.
         *
         * @param: None
         * @return: None
         * @post-cond: A button floating on top of the screen can be used to control the service
         *             by the user if the app have all the permissions it needs. Else opens settings
         *             page with the app's details.
         * */

        super.onServiceConnected();
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        Date date = new Date();
        currentTime = date.getTime();
//        try {
//            dictionary = new Dictionary();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
        //loadData();
        loadAPIConnection();
        getDisplayMetrics();
        currentSource = getRootInActiveWindow();
        currentPackageName = currentSource.getPackageName().toString();
        updateScreenXML();
        loadCurrentActivityName();
        graph = new Graph(currentSource.getPackageName().toString(), getApplicationContext());
//        graph = new Graph("", getApplicationContext());
        currentNodeGraph = graph.getNodeByXML(currentScreenXML);
        if (currentNodeGraph == null){
            loadCurrentNodeGraph();
        }
        serviceInfo = new AccessibilityServiceInfo();
        serviceInfo.flags |= AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;
        serviceInfo.flags |= AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS;
        setServiceInfo(serviceInfo);


        Log.d("GRAPH", graph.toString());
        Log.d(debugLogTag, "Service Connected");
        loadAppNames();
        //createText2VecModel();

    }

    private void loadAppNames() {
        final PackageManager pm = getPackageManager();
        List<ApplicationInfo> packages = pm.getInstalledApplications(PackageManager.GET_META_DATA); // getting meta data of all installed apps

        for (ApplicationInfo packageInfo : packages) {          // checking if the input has a match with app name
            try {
                ApplicationInfo info = pm.getApplicationInfo(packageInfo.packageName, PackageManager.GET_META_DATA);
                String appName = (String) pm.getApplicationLabel(info).toString().toLowerCase();
                this.appNames.add(appName);
            } catch (PackageManager.NameNotFoundException e) {
                e.printStackTrace();                // handling app not found exception
            }
        }
        Log.d("Apps", this.appNames.toString());
    }

    String getActionDescription(int eventType) {
        switch (eventType) {
            case AccessibilityEvent.TYPE_VIEW_CLICKED:
                return "View Clicked";
            case AccessibilityEvent.TYPE_VIEW_LONG_CLICKED:
                return "View Long Clicked";
            case AccessibilityEvent.TYPE_VIEW_SCROLLED:
                return "View Scrolled";
            case AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED:
                return "Text Changed";
            default:
                return null;  // 只处理上述类型，其他类型可根据需要添加
        }
    }

    private void updateGraphDB(String target, String action, String bounds) {

        String cacheXML = currentScreenXML;
        Log.d("DEBUG","1");
        while (currentScreenXML.equals(cacheXML)) {
            wait(1);
            autoReload();
        }
        autoReload();
        getAppDescription(target, action, bounds);


    }

    public static void wait(int second) {
        try {
            TimeUnit.SECONDS.sleep(second);
        } catch (InterruptedException e) {
            Log.e("ERROR", "sleep failed");
        }
    }

    public void autoReload() {
        if (currentSource != null) {
            currentSource.refresh();
            if (isNotBlockedEvent())
                updateScreenXML();
        }


    }

    public void getAppDescription(String target, String action, String bounds) {
            String summarisePrompt = Command.screenSummarise(currentScreenXML, getAppNameFromPackageName(currentSource.getPackageName().toString()), currentSource.getPackageName().toString(), currentActivityName);
            Log.d("summarise_prompt", summarisePrompt);
            Call<ChatResponseObject> call = jsonApi.getDataChat(
                    new ChatRequestBody(summarisePrompt)
            );
            call.enqueue(new Callback<ChatResponseObject>() {
                @Override
                public void onResponse(Call<ChatResponseObject> call, Response<ChatResponseObject> response) {
                    if (!response.isSuccessful()) {
                        assert response.errorBody() != null;

                        try {
                            Log.e("myErrTag", response.errorBody().string());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                        return;
                    }
                    ChatResponseObject data = response.body();
                    if (data != null && data.choices != null && data.choices.size() > 0) {
                        //String text = data.choices.get(0).text;
                        String text = data.choices.get(0).message.content;
                        Log.d("SUMMARISE", text);

                        Node newNode = graph.addNode(currentActivityName, Utils.clickableElementAsString(currentSource), text, currentScreenXML);
                        Edge edge = new Edge(currentNodeGraph, newNode, action, target, bounds);
                        currentNodeGraph = newNode;
                        Log.d("CurrentNode:",currentNodeGraph.toString());
                        graph.addEdge(edge);

                    }
                }

                @Override
                public void onFailure(Call<ChatResponseObject> call, Throwable t) {
                    Log.e("myErrTag", t.getMessage());
                }
            });

        Log.d("GRAPH", graph.toString());
    }

    public void setCurrentActName(AccessibilityEvent event) {

        String packageName = String.valueOf(event.getPackageName());
        PackageManager pm = getPackageManager();
        Intent intent = pm.getLaunchIntentForPackage(packageName);
        if (intent != null) {
            ComponentName componentName = intent.getComponent();
            if (!componentName.getClassName().contains("ReadManifest"))

                currentActivityName = componentName.getClassName();
        }

        if (currentSource != null && currentSource.getPackageName() != null && !currentSource.getPackageName().toString().equals(currentPackageName)) {
            Log.d("PACKAGE_NAME_CHANGE", currentPackageName + "->" + currentSource.getPackageName());
            currentPackageName = currentSource.getPackageName().toString();

            graph = new Graph(currentPackageName, getApplicationContext());
        }
    }

//    public void requestPressAction() {
//
//        String pressPrompt = Command.pressPrompt(currentCommand, currentTooltipCount + "", currentScreenXML, getAppNameFromPackageName(currentSource.getPackageName().toString()), currentSource.getPackageName().toString(), chatHistory.getChatHistory(), currentActivityName);
//        //Log.d("prompt",pressPrompt);
//        Call<ResponseObject> call = jsonApi.getData(
//                new RequestBody(pressPrompt)
//        );
//        call.enqueue(new Callback<ResponseObject>() {
//            @Override
//            public void onResponse(Call<ResponseObject> call, Response<ResponseObject> response) {
//                if (!response.isSuccessful()) {
//                    assert response.errorBody() != null;
//
//                    try {
//                        Log.e("myErrTag", response.errorBody().string());
//                    } catch (IOException e) {
//                        e.printStackTrace();
//                    }
//                    return;
//                }
//                ResponseObject data = response.body();
//                if (data != null && data.choices != null && data.choices.size() > 0) {
//                    String text = data.choices.get(0).text;
//                    Log.d("CLICK", text);
//
//                    String[] elements = text.split("###");
//
//                    String target = elements[2].split(":")[1].trim();
//
//                    if (elements[3].split(":").length > 1) {
//                        String bounds = elements[3].split(":")[1].trim();
//                        String[] arr = bounds.substring(1, bounds.length() - 1).replaceAll("\\]\\s*\\[", ",").split(","); // split into pairs
//                        int[] arrInt = new int[4]; // create array of appropriate size
//                        int index = 0;
//                        for (String str : arr) {
//
//                            arrInt[index++] = Integer.parseInt(str); // add first number to array
//
//                        }
//                        updateGraphDB(target, "PRESS", bounds);
//                    } else {
//                        updateGraphDB(target, "PRESS", " ");
//                    }
//
//
//                }
//            }
//
//            @Override
//            public void onFailure(Call<ResponseObject> call, Throwable t) {
//                Log.e("myErrTag", t.getMessage());
//            }
//        });
//    }



    public String getAppNameFromPackageName(String packageName) {
        final PackageManager pm = getApplicationContext().getPackageManager();
        ApplicationInfo ai;
        try {
            ai = pm.getApplicationInfo(packageName, 0);
        } catch (final PackageManager.NameNotFoundException e) {
            ai = null;
        }
        return (String) (ai != null ? pm.getApplicationLabel(ai) : "<unk>");

    }


    public boolean isNotBlockedEvent() {
        Date date = new Date();
        long time = date.getTime();
        if (time - currentTime > 1000) {
            currentTime = time;
            return true;
        }

        return false;
    }

    void loadData() {

        mPrefs = getSharedPreferences(FILE_NAME, 0);
        Gson gson = new Gson();
        String json = mPrefs.getString("packageDataObjects", "");
        Type type = new TypeToken<ArrayList<PackageDataObject>>() {
        }.getType();
        packageDataObjects = gson.fromJson(json, type);
        componentAsString = getAppComponentAsString();
    }

    private String listToString(ArrayList<String> list) {
        StringBuilder output = new StringBuilder();
        for (String ui : list) {
            output.append(ui);
            output.append(", ");
        }
        String outputAsString = output.toString();
        if (outputAsString.length() > 2) {
            return outputAsString.substring(0, outputAsString.length() - 2);
        } else {
            return outputAsString;
        }
    }

    String getAppComponentAsString() {

        StringBuilder output = new StringBuilder();
        ArrayList<String> systemApp = new ArrayList<>(Arrays.asList("voicify", "meet", "google services framework", "speech services by google", "home", "keep notes", "google vr services", "pixel ambient services", "google connectivity services", "default print service", "live transcribe & sound notifications", "pixel wallpapers 18", "nfc service", "android accessibility suite", "pixel ambient service", "127", "android system intelligence", "select hour", "start date – %1$s", "sim manager", "call management", "markup", "android system webview", "true", "package installer", "work setup", "pixel launcher", "google wallet", "settings services", "bluetooth", "150", "220", "styles & wallpapers", "android auto", "adaptive connectivity services", "device health services", "carrier setup", "live wallpaper picker", "android auto", "clear text", "pixel buds", "google wi-fi provisioner", "system ui", "system tracing", "gboard", "smart storage", "wireless emergency alerts", "playground", "media storage", "false", "device setup", "google tv", "android system", "pixel setup", "nfc", "personal safety", "current selection: %1$s", "extreme battery saver"));
        for (PackageDataObject packageDataObject : packageDataObjects) {
            if (packageDataObject.name.contains(".") || systemApp.contains(packageDataObject.name)) {
                continue;
            }
            ArrayList<String> commonWords = new ArrayList<>(Arrays.asList("app", "apps", "application", "http", "https", "deeplink", "com", "android", "intent", "action", "google", "VIEW", "MAIN"));
            List<String> appWords = Arrays.asList(packageDataObject.packageName.split("\\."));
            ArrayList<String> components = new ArrayList<>();
            for (String deeplink : packageDataObject.deepLinks) {
                String[] words = deeplink.split("[^\\w']+");
                String prefix = words[words.length - 1].toLowerCase(Locale.ROOT);
                if (!appWords.contains(prefix) && !commonWords.contains(prefix) && !components.contains(prefix) && prefix.length() > 1) { //&& dictionary.contains(prefix)
                    components.add(prefix);
                }
            }
            for (String intent : packageDataObject.getQuerySearch("")) {
                String[] words = intent.split("[^\\w']+");
                ArrayList<String> keywords = new ArrayList<>();
                for (String word : words) {
                    if (!appWords.contains(word) && !commonWords.contains(word)) {
                        if (word.endsWith("Activity")) {

                            keywords.add(word.replace("Activity", ""));
                        } else if (word.endsWith("Launcher")) {

                            keywords.add(word.replace("Launcher", ""));
                        } else if (word.contains("_")) {

                            word.replace("_", " ");
                        } else {
                            keywords.add(word);
                        }

                    }
                }
                ArrayList<String> finalSet = new ArrayList<>();
                for (String keyword : keywords) {
                    String[] singleWords = keyword.split("(?<!(^|[A-Z]))(?=[A-Z])|(?<!^)(?=[A-Z][a-z])");
                    String element = String.join(" ", singleWords);
                    element = element.replace("MAIN", "").replace("VIEW", "");

                    if (!finalSet.contains(element.toLowerCase(Locale.ROOT))) { //&& dictionary.contains(element)
                        finalSet.add(element.toLowerCase(Locale.ROOT));
                    }
                }
                String componentName = String.join(" ", finalSet);
                if (!components.contains(componentName.toLowerCase(Locale.ROOT))) {
                    components.add(componentName.toLowerCase(Locale.ROOT));

                }

            }
            String outputStr = packageDataObject.name + " APP has COMPONENT: " + listToString(components) + ".\n";
            output.append(outputStr);
        }

        return output.toString();
    }

    void loadAPIConnection() {
        Gson gson = new GsonBuilder()
                .setLenient()
                .create();
        retrofit = new Retrofit.Builder()
                .baseUrl("https://api.openai.com/")
                .addConverterFactory(GsonConverterFactory.create(gson))
                .build();
        jsonApi = retrofit.create(JsonApi.class);
    }

    private void getDisplayMetrics() {
        DisplayMetrics metrics = getApplicationContext().getResources().getDisplayMetrics();
        width = metrics.widthPixels;
        height = metrics.heightPixels;
    }

    private void loadCurrentNodeGraph(){
        String summarisePrompt = Command.screenSummarise(currentScreenXML, getAppNameFromPackageName(currentSource.getPackageName().toString()), currentSource.getPackageName().toString(), currentActivityName);
        Log.d("summarise_prompt", summarisePrompt);
        Call<ChatResponseObject> call = jsonApi.getDataChat(
                new ChatRequestBody(summarisePrompt)
        );
        call.enqueue(new Callback<ChatResponseObject>() {
            @Override
            public void onResponse(Call<ChatResponseObject> call, Response<ChatResponseObject> response) {
                if (!response.isSuccessful()) {
                    assert response.errorBody() != null;

                    try {
                        Log.e("myErrTag", response.errorBody().string());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    return;
                }
                ChatResponseObject data = response.body();
                if (data != null && data.choices != null && data.choices.size() > 0) {
                    //String text = data.choices.get(0).text;
                    String text = data.choices.get(0).message.content;
                    Log.d("SUMMARISE", text);
                    currentNodeGraph = graph.addNode(currentActivityName, Utils.clickableElementAsString(currentSource), text, currentScreenXML);
                    Log.d("CurrentNode:",currentNodeGraph.toString());
                }
                Log.d("GRAPH", graph.toString());
            }

            @Override
            public void onFailure(Call<ChatResponseObject> call, Throwable t) {
                Log.e("myErrTag", t.getMessage());
            }
        });

    }

    private void loadCurrentActivityName(){
        PackageManager pm = getPackageManager();
        Intent intent = pm.getLaunchIntentForPackage(currentPackageName);
        if (intent != null) {
            ComponentName componentName = intent.getComponent();
            if (!componentName.getClassName().contains("ReadManifest"))

                currentActivityName = componentName.getClassName();
        }
    }

    private void createSwitch() {
        /**
         * This code will create a layout for the switch. This code is called whenever service is
         * connected and will be gone when service is shutdown
         *
         */

        // Check for permissions
        int LAYOUT_FLAG;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            LAYOUT_FLAG = WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY;
        } else {
            LAYOUT_FLAG = WindowManager.LayoutParams.TYPE_PHONE;
        }
        mLayout = new FrameLayout(this);

        // Create layout for switchBar
        switchBar = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                LAYOUT_FLAG,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);
        switchBar.gravity = Gravity.TOP;  // stick it to the top
        //WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL |


        LayoutInflater inflater = LayoutInflater.from(this);
        View actionBar = inflater.inflate(R.layout.action_bar, mLayout);
        wm.addView(mLayout, switchBar);       // add it to the screen


        startButton = mLayout.findViewById(R.id.listenBtn);
        dumpBtn = mLayout.findViewById(R.id.resetBtn);
        // textMsg = mLayout.findViewById(R.id.msg);
        //  inputTxt = mLayout.findViewById(R.id.inputTxt);
        //  inputTxt.setBackgroundResource(R.color.black);
        startButton.setBackgroundResource(R.drawable.start_btn);
        configureStartButton();
        configureDumpButton();
    }

    private void configureStartButton() {
        /**
         * This function is called after the service has been connected. This function binds
         * functionality to the master button which can be used to turn on/off the tool.
         *
         * @param: None
         * @return: None
         * @post-cond: functionality has been added to the inflated button
         * */

        startButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                if (startButton.getText().toString().equalsIgnoreCase("start")) {
                    startButton.setText("Stop");
                    startButton.setBackgroundResource(R.drawable.stop_btn);
                    isStarted = true;
                } else {
                    startButton.setText("Start");

                    startButton.setBackgroundResource(R.color.transparent);
                    isStarted = false;
                    startButton.setBackgroundResource(R.drawable.start_btn);
                    //         textMsg.setText("");
                }
            }
        });
    }

    private void configureDumpButton() {
        /**
         * This function is called after the service has been connected. This function binds
         * functionality to the master button which can be used to turn on/off the tool.
         *
         * @param: None
         * @return: None
         * @post-cond: functionality has been added to the inflated button
         * */

        dumpBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                getScreenShot();
                getXML();
            }
        });
    }

    private void getXML() {
        XmlSerializer serializer = Xml.newSerializer();
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        try {
            serializer.setOutput(outputStream, "UTF-8");
            serializer.startDocument(null, true);
            AccessibilityNodeInfoDumper.dumpNodeRec(getRootInActiveWindow(), serializer, 0, false, width, height, false);
            serializer.endDocument();
            String xml = outputStream.toString("UTF-8");
            File file = new File(getApplicationContext().getExternalFilesDir("screenshots"),"screenshot.png");
            if (!file.exists()) {
                file.createNewFile();
            }
            FileOutputStream fos = new FileOutputStream(file);
            OutputStreamWriter osw = new OutputStreamWriter(fos);
            osw.write(xml);
            osw.close();
            fos.flush();
            fos.close();

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void getScreenShot() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Display display = getDisplay();
            if(display != null) {
                takeScreenshot(display.getDisplayId(), getMainExecutor(), new TakeScreenshotCallback() {
                    @Override
                    public void onSuccess(@NonNull ScreenshotResult screenshotResult) {
                        Bitmap bitmap = Bitmap.wrapHardwareBuffer(screenshotResult.getHardwareBuffer(), screenshotResult.getColorSpace());
                        try {
                        File file = new File(getApplicationContext().getExternalFilesDir("screenshots"),"screenshot.png");
                        if (!file.exists()) {
                            file.createNewFile();
                        }
                        FileOutputStream fos = new FileOutputStream(file);
                        bitmap.compress(Bitmap.CompressFormat.PNG, 100, fos);
                        fos.flush();
                        fos.close();
                        } catch (IOException e) {
                            System.err.println("Error saving screenshot: " + e);
                        }
                    }

                    @Override
                    public void onFailure(int i) {
                        Log.e("Error","截图获取失败");
                    }
                });
            }
        }

    }
    private int getStatusBarHeight() {
        int result = 0;
        int resourceId = getResources().getIdentifier("status_bar_height", "dimen", "android");
        if (resourceId > 0) {
            result = getResources().getDimensionPixelSize(resourceId);
        }
        return result;
    }

    @Override
    public boolean onTouch(View view, MotionEvent motionEvent) {
        return false;
    }
}



