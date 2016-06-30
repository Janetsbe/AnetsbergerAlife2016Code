using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine.UI;



/* This class handles all events and functionality relating to the robot simulation.
 */
public class RobotSimulation: MonoBehaviour {
    //Database variables
    DatabaseHandler dbHandler;
    public bool rerun;

    //Class level constants.
    public const int SIMPLE_NPARTS = 3;
    public const int COMPLEX_NPARTS = 7;
    public const float MESSAGE_CHECK_TIMER = .25f;


    //Declarations for variables relating to camera functionality.
    Vector3 camVelocity;
    public Vector3 camLookOffset = new Vector3(-7, 3, 0);
    public Vector3 initialCameraPosition = new Vector3(-14f, 10f, 14f);
    public bool cameraTracking;



    public float timeScale;


    //Variables relating to GUI elements
    public Text commandBox;
    public Text teachPromptText;
    public Text commandPromptText;
    public Text promptText;
    public Text commandPromptLow;
    public Text commandPromptMid;
    public Text teachPromptLow;
    public Text teachPromptMidA;
    public Text teachPromptHighA;
    public Text teachPromptMidB;
    public Text teachPromptHighB;
    public Text commandTimer;
    public Text commandTimerLabel;
    public Text teachTimer;
    public Text infoText;
    public Text robotIDText;

    public static string infoTextContents;
    float commandTimeLeft;
    float teachTimeLeft;

    public RawImage yesSignal;
    public RawImage noSignal;
    public RawImage rs;

    public GameObject rewardBarHolder;
    public GameObject commandGraphHolder;
    public GameObject commandBarPrefab;
    public GameObject userNamePopupPrefab;


    //Declaration of variables relating to dynamic user input fields.
    List<string> commandUserQueue = new List<string>();
    List<string> rewardUserQueue = new List<string>();
    List<GameObject> commandBars = new List<GameObject>();
    public string[] mostCommonCommands;
    public string[] mostCommonCommandCounts;
    public int reward;
    public int punish;


    //Variables corresponding to robot parameters.
    public int numParts;
	public string robotColor;
	public string command;
    public string robotType;
    public string robotID;
	public int numJoints;
	int jointLimit; //in degrees
	HingeJoint[] joints;
	GameObject[] robotParts;
	public float[ , ] jointActuationCoefficients;
    public string[] validRewards;

	public GameObject floor;
	public Texture2D floorTexture;
    public Texture2D eyeTexture;

    int time;
    float timer;

	bool paused = false;
    public bool endRun = false;
    public bool useExternalData;
    public bool lastController;
    public bool hasCommand;

    public float springForce = 40;

    List<int[]> sensorData;
    int[] sensorValues;

    public Dictionary<string, Color> colors;


    // Use this for initialization
    void Start () {
        string dbName = rerun ? "rerunDB" : "tpevorobots";
        dbHandler = new DatabaseHandler(dbName);
    

        print("info text contents: " + infoTextContents);
        infoText.text = infoTextContents;

        camVelocity = Vector3.zero;
        transform.position = initialCameraPosition;
        transform.LookAt(floor.transform.position + camLookOffset);
        Time.timeScale = timeScale;

        validRewards = new string[2];
        colors = SetupColors();
        reward = 0;

        SetupRobotValues();
        hasCommand = !command.Equals("none");
        robotIDText.text = robotID;

        CheckForCommands();
        RefreshCommandGraph(true) ;
        SetupTextBoxes();
        RefreshUITimers();

        timer = MESSAGE_CHECK_TIMER;
        time = 0;

        jointLimit = 75;
		robotParts = new GameObject[numParts];
		joints = new HingeJoint[numJoints];

		SetupFloor();

        commandTimeLeft = dbHandler.ReadFromDB<float>("commandTimeLeft");
        teachTimeLeft = dbHandler.ReadFromDB<float>("instanceTimeLeft");

        sensorData = new List<int[]>();
        sensorValues = new int[numParts];

        if (robotType.Equals("simple")) {
		    CreateSimpleRobot(1.0f, 0f, 0f);
        }
        else {
            CreateComplexRobot();
        }

        if(rerun) {
            dbHandler.ClearSensorData(robotID);
        }
	}


    //Called once per physics timestep. All physics and physics 
    //related functionality (e.g. timestep counting) should be performed here
	void FixedUpdate () {

        for(int i = 0; i < numParts; i++){
            sensorValues[i] = robotParts[i].GetComponent<SensorHandler>().value;
        }
        
        sensorData.Add(sensorValues);
        dbHandler.WriteSensorDataRow(sensorValues, robotID);
        //print(time + ": " + string.Join(", ", System.Array.ConvertAll(sensorData[time], x => x.ToString())));
        //print(string.Join(", ", System.Array.ConvertAll(sensorData[time], x => x.ToString())));

		if(time % 1 == 0 && robotParts[0] != null && time > 50) {
			RunMotors();
		}


        if (time % 500 == 0) {
            dbHandler.WritePosition(robotParts[1].transform.position.ToString() + 
                                 ", " +  robotParts[0].transform.position.ToString(), robotID, rerun);
        }

        if(cameraTracking) {
            Quaternion targetRotation = Quaternion.LookRotation(robotParts[1].transform.position + camLookOffset - transform.position);
            gameObject.transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, .00001f * Time.deltaTime);//robotParts[1].transform.position + new Vector3(-7, 4, 0));
            gameObject.transform.position = Vector3.SmoothDamp(transform.position,
                                                   initialCameraPosition + robotParts[1].transform.position,
                                                   ref camVelocity, 2f);
        }	
        time++;
	}
	
	
	// Update is called once per frame
	void Update () {
        UpdateUserQueue();
        RefreshUITimers();
        CheckForInput();
        timer -= Time.deltaTime;
        if (timer <= 0) {
            timer = MESSAGE_CHECK_TIMER;
            CheckForMessage();
            RefreshCommandGraph(false);
            GenerateUserCommandPopup();
            infoTextContents = infoText.text;
            if(hasCommand) {
                GenerateUserRewardPopup();
            }
        }
  		if(endRun) {
            endRun = false;
            //dbHandler.WriteSensorData(sensorData.ToArray(), robotID);
			RestartSimulation();
		}
	}



    //Prepares GUI elements with appropriate text based on the current robot, command, etc.
    void SetupTextBoxes() {
        commandPromptText.supportRichText = true;
        bool hasNoCommand = command.Equals("none");

        string colorMarkup = "<color=#" + ColorToHex(colors[robotColor]) + ">";
        string topLevelPrompt = "If you want to...";
        string commandPrompt = "...command the next robots...";
        string commandPromptDetails= "...just tell them what to do in chat.";

        string teachPromptNoCommand = "...teach a robot...";
        string teachPromptHasCommand = "...teach the " + "[" + colorMarkup + robotColor.ToCharArray()[0] 
                                        + "</color>]" + robotColor.Substring(1) + " robot...";
        string teachPrompt = hasNoCommand ? teachPromptNoCommand : teachPromptHasCommand;

        string ifYes = "...say '" + colorMarkup + validRewards[0] + "</color>\'";
        string ifYesHigh = "...if [" + colorMarkup + "y</color>]es, it's obeying the command: "+ "\n\n\"" 
                            + colorMarkup + command + "</color>\""; 
        string ifNo =   "...say '" + colorMarkup + validRewards[1] + "</color>\'";
        string ifNoHigh = "...If [" + colorMarkup + "n</color>]o, it's not.";
        string teachPromptDetails = hasNoCommand ? teachPromptNoCommand : teachPromptHasCommand;

        promptText.text = topLevelPrompt;
        commandPromptLow.text = commandPrompt;
        commandPromptMid.text = commandPromptDetails;
        teachPromptLow.text = teachPrompt;
        teachPromptMidA.text = hasNoCommand ? "...first, enter some commands!" : ifYes;
        teachPromptHighA.text = hasNoCommand ? "" : ifYesHigh;
        teachPromptMidB.text = hasNoCommand ? "" : ifNo;
        teachPromptHighB.text = hasNoCommand ? "" : ifNoHigh;

        teachPromptHighB.gameObject.SetActive(hasCommand);
        yesSignal.transform.parent.gameObject.SetActive(hasCommand);
        noSignal.transform.parent.gameObject.SetActive(hasCommand);
    }


    void SetupRobotValues() {
        //Use data from the DB collection "messages".
        if (useExternalData) {
            robotType = (string) dbHandler.ReadFromDB<string>("robotType");
            robotColor = (string) dbHandler.ReadFromDB<string>("color");
            command = (string) dbHandler.ReadFromDB<string>("command");
            robotID = dbHandler.ReadFromDB<string>("robotID");
            print("robotType: " + robotType);
            numParts = robotType.Equals("simple") ? SIMPLE_NPARTS : COMPLEX_NPARTS;
            numJoints = numParts - 1;
            jointActuationCoefficients = new float[numJoints, 3];
            jointActuationCoefficients = dbHandler.ReadController(numJoints);

            springForce = robotType.Equals("simple") ? 500f : 800.0f;
        }
        else {
            numParts = robotType.Equals("simple") ? SIMPLE_NPARTS : COMPLEX_NPARTS;
            numJoints = numParts - 1;
            GetActuationCoefficients(jointActuationCoefficients);
        }
        validRewards = new string[] { robotColor.ToCharArray()[0] + "y", robotColor.ToCharArray()[0] + "n" };
	}


    //Iterates over every joint and actuates it. Angle is a function of timestep and coefficients.
	void RunMotors() {
		for(int i = 0; i < numJoints; i++) {
            float angle = (float) (180 * (jointActuationCoefficients[i, 0] *
                                    System.Math.Sin(time * jointActuationCoefficients[i, 1]
                                    + jointActuationCoefficients[i, 2])) / Mathf.PI);
            angle = i > 2 ? Mathf.Abs(angle) : angle;
            angle = (robotType.Equals("complex") && i < 3) ? angle / 2 : angle;
            ActuateJoint(i, angle);
		}
	}

	/*Actuates joints using hinge joint's spring functionality
     * which "springs" (pulls) a joint towards a specified angle */
	void ActuateJoint(int index, float targetAngle) {
        joints[index].useSpring = true;
        JointSpring spring = joints[index].spring;
        spring.targetPosition = targetAngle;
        spring.spring = springForce;
        joints[index].spring = spring;
	}
	


	void CreateComplexRobot() {
		float length = 3.0f;
		float height = .4f;
		float width = 1.2f;
        float bodyLimit = jointLimit / 2;
        float armLimitMin = jointLimit;
        float armLimitMax = jointLimit / 8;

        //Create the main body segments.
        for (int i = 0; i < 3; i++) {
		    CreateSegment(i,   0f, 1f, (-((numParts-4) * length)/2 + length/2) + length * i ,   
                          width, height, length, 0, 0, 0);
        }
        CreateJoint(0, 0, 1, -bodyLimit, bodyLimit, Vector3.up);
        CreateJoint(1, 1, 2, -bodyLimit, bodyLimit, Vector3.up);
        
        //Create legs and their joints
        CreateSegment(3, (width/2f + length/2f), 1f, robotParts[0].transform.position.z,
                          width/2, height, length, 0, -90, 0);
        CreateJoint(2, 3, 0,     -armLimitMin, -armLimitMax, Vector3.right);
        

		CreateSegment(4, -(width / 2f + length / 2f), 1f, robotParts[0].transform.position.z,
                                  width/2, height, length, 0, 90, 0);
        
		CreateJoint(3, 4, 0,     -armLimitMin, -armLimitMax, Vector3.right);
        

		CreateSegment(5, (width / 2f + length / 2f), 1f, robotParts[2].transform.position.z,
                                  width/2, height, length, 0, -90, 0);
		CreateJoint(4, 5, 2,     -armLimitMin, -armLimitMax, Vector3.right);

		CreateSegment(6, -(width/2f + length/2f), 1f, robotParts[2].transform.position.z,
                                  width/2, height, length, 0, 90, 0);
		CreateJoint(5, 6, 2,     -armLimitMin, -armLimitMax, Vector3.right);
		
	}
	
	
	
	void CreateSimpleRobot(float scale, float x, float z) {
		//print("create robot");
		//

		float length = 2.5f;
		float height = .6f;
		float width = 3.0f;

		for(int i = 0; i < numParts; i++) {

            CreateSegment(i, 0f, 1f, (-(numParts * length) / 2 + length / 2) + length * i,
                        width, height, length, 0, 0, 0);
            robotParts[i].GetComponent<Rigidbody>().constraints = RigidbodyConstraints.FreezeRotationY;
            robotParts[i].GetComponent<Rigidbody>().constraints = RigidbodyConstraints.FreezePositionX;
            //robotParts[i].GetComponent<Rigidbody>().constraints = RigidbodyConstraints.FreezeRotationZ;

		}

		for(int i = 0; i < numJoints; i++) { 
			CreateJoint(i, i, i + 1, -jointLimit, jointLimit, Vector3.right);
		}
	

	}
	
	
	void CreateSegment(int index, float x, float y, float z, float width, float height, float length, float xrot, float yrot, float zrot) {
		Vector3 position = new Vector3(x, y, z);
		Vector3 size = new Vector3(width, height, length);
        Vector3 rotation = new Vector3(xrot, yrot, zrot);
		
		robotParts[index] = GameObject.CreatePrimitive(PrimitiveType.Cube);

        Color color;
        color = colors.TryGetValue(robotColor, out color) ? color : Color.white;

        robotParts[index].GetComponent<Renderer>().material.color = color;
		robotParts[index].transform.position = position;
		robotParts[index].transform.localScale = size;
        
		robotParts[index].AddComponent<Rigidbody>();
		robotParts[index].name = "Robot Body " + index;
		robotParts[index].GetComponent<Rigidbody>().collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
    
        robotParts[index].transform.eulerAngles = rotation;
        robotParts[index].GetComponent<Rigidbody>().mass = 4f;

        SensorHandler sh = robotParts[index].AddComponent<SensorHandler>();
        sh.parentIndex = index;
    
        //place eyes on the appropriate body segment.
        if (index == 2) {
            CreateEyes(index);
        }
    }


    void CreateEyes(int index) {
        float eyeSize = robotType.Equals("simple") ? .7f : .4f;
 
        GameObject lEye = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        GameObject rEye = GameObject.CreatePrimitive(PrimitiveType.Sphere);

        lEye.transform.localScale = new Vector3(eyeSize, eyeSize, eyeSize);
        lEye.transform.parent = robotParts[index].transform;
        lEye.transform.localPosition = new Vector3(.2f, .5f, .48f);
        lEye.GetComponent<Renderer>().material.mainTexture = eyeTexture;
        lEye.transform.eulerAngles = new Vector3(0, 180, 0);
        Destroy(lEye.GetComponent<SphereCollider>());

        rEye.transform.localScale = new Vector3(eyeSize, eyeSize, eyeSize);
        rEye.transform.parent = robotParts[index].transform;
        rEye.transform.localPosition = new Vector3(-.2f, .5f, .48f);
        rEye.GetComponent<Renderer>().material.mainTexture = eyeTexture;
        rEye.transform.eulerAngles = new Vector3(0, 180, 0);
        Destroy(rEye.GetComponent<SphereCollider>());
    }
	
	
	void CreateJoint(int index, int fromIndex, int toIndex, float limitMin, float limitMax, Vector3 axis) {
		joints[index] = robotParts[fromIndex].AddComponent<HingeJoint>();
		joints[index].axis = axis;
		joints[index].connectedBody = robotParts[toIndex].GetComponent<Rigidbody>();
		joints[index].anchor = new Vector3(0f, 0f, .5f);
		joints[index].autoConfigureConnectedAnchor = true;

		JointLimits limits = joints[index].limits;
		limits.min = limitMin;	
		limits.max = limitMax;

		joints[index].limits = limits;
		joints[index].useLimits = true;
	}
	

	void DestroyRobot() {
        print("destroying robot");
		for(int i = 0; i < numParts; i++) {
            Destroy(robotParts[i]);
			robotParts[i] = null;
		}
		Resources.UnloadUnusedAssets(); //needed to prevent memory leak.
	}
	
	
	void SetupFloor() {
		floor.GetComponent<Renderer>().material.mainTexture = (Texture) floorTexture;
		floor.GetComponent<Renderer>().material.mainTextureScale = new Vector2(floor.transform.localScale.x / 4, floor.transform.localScale.z / 4);
	}
	
	
	void RestartSimulation() {
        print("resetting simulation");
        Resources.UnloadUnusedAssets();
        if (robotParts[0] != null) {
			DestroyRobot();
		}
        dbHandler.CloseConnection();
        System.Threading.Thread.Sleep(250);
	    Application.LoadLevel("Main Scene");
	}

	
	void CheckForInput() {
		if(Input.GetKeyUp("space")) {
			RestartSimulation();
		}
		if(Input.GetKeyUp("p")) {
			paused = !paused;
			if(paused) {
				Time.timeScale = 0;
			}
			else {
				Time.timeScale = 1;
			}
		}		
	}
	

	Dictionary<string, Color> SetupColors() {
        Dictionary<string, Color> dict = new Dictionary<string, Color>();
        dict.Add("red", new Color(.5f, .1f, .1f));
        dict.Add("orange", new Color(1.0f, .4f, .0f));
        dict.Add("yellow", Color.yellow);
        dict.Add("green", new Color(.1f, .4f, .1f));
        dict.Add("blue", Color.blue);
        dict.Add("violet", new Color(.7f, .1f, .7f));
        return dict;
    }
    

    private void UpdateUserQueue() {
        commandUserQueue.AddRange(dbHandler.ReadFromDB<string[]>("commandUserQueue"));
        dbHandler.WriteToDB<string[]>("commandUserQueue", new string[0]);
        rewardUserQueue.AddRange(dbHandler.ReadFromDB<string[]>("rewardUserQueue"));
        dbHandler.WriteToDB<string[]>("rewardUserQueue", new string[0]);
    }


    private void GenerateUserRewardPopup() {
        if(rewardUserQueue.Count > 0) {
            string[] userReward = rewardUserQueue[0].Split(':');
            rewardUserQueue.RemoveAt(0);

            string userName = userReward[0];
            string rewardSignal = userReward[1].ToCharArray()[1] + "";
            //print(rewardSignal);
            Transform parentSignalBar = (rewardSignal.Equals("y") ? teachPromptMidA : teachPromptMidB).transform.Find(rewardSignal + "Signal");
            //print(parentSignalBar);
            GameObject userPopup = (GameObject)Instantiate(userNamePopupPrefab,
                                        Vector3.zero,
                                        Quaternion.identity) as GameObject;
            UserNameHandler userPopupHandler = userPopup.GetComponent<UserNameHandler>();
            userPopupHandler.parentCommandLabel = parentSignalBar;
            userPopupHandler.userName = userName;
            userPopupHandler.duration = 90;
            userPopupHandler.initialPosition = parentSignalBar.transform.Find("bar").position + 180 * Vector3.right;
        }
    }


    private void GenerateUserCommandPopup() {
        bool topFound = false;
        string userName = null;
        string commandWord = null;
        while(commandUserQueue.Count > 0 && !topFound) {
            string[] userCommand = commandUserQueue[0].Split(':');
            commandUserQueue.RemoveAt(0);
            try {
                foreach (string word in mostCommonCommands) {
                    if (word.Equals(userCommand[1])) {
                        commandWord = userCommand[1];
                        userName = userCommand[0];
                        topFound = true;
                    }
                }
            } catch {
                print("ERROR: no most common commands");
            }
        }

        if (commandWord != null) {
            Transform parentCommandBar = commandGraphHolder.transform.Find(commandWord);
            GameObject userPopup = (GameObject)Instantiate(userNamePopupPrefab,
                                        Vector3.zero,
                                        Quaternion.identity) as GameObject;
            UserNameHandler userPopupHandler = userPopup.GetComponent<UserNameHandler>();
            userPopupHandler.parentCommandLabel = parentCommandBar;
            userPopupHandler.userName = userName;
            userPopupHandler.duration = 108;
            userPopupHandler.initialPosition = parentCommandBar.transform.Find("bar").position + 200 * Vector3.right;
        }
    }

    private void RefreshUITimers() {

        commandTimeLeft -= Time.deltaTime/Time.timeScale;
        teachTimeLeft -= Time.deltaTime/Time.timeScale;

        commandTimeLeft = (commandTimeLeft < 0.0f || teachTimeLeft > 999) ? 0.0001f : commandTimeLeft;
        teachTimeLeft = (teachTimeLeft < 0.0f || teachTimeLeft > 999) ? 0.0001f : teachTimeLeft;

        string[] commandTime = commandTimeLeft.ToString().Split('.');
        string[] teachTime = teachTimeLeft.ToString().Split('.');
        try {
            commandTimer.text = commandTime[0] + "s";// + "." + commandTime[1].Substring(0, 2);
            teachTimer.text = teachTime[0] + "s";// + "." + teachTime[1].Substring(0, 2);
        }catch{
            print("timeFormat Error");
        }
    }



    private void RefreshCommandGraph(bool setCount) {
        try {
            for(int i = 0; i < mostCommonCommands.Length; i++) {
                try {
                    commandBars[i].ToString();
                }catch{
                    commandBars.Add((GameObject)Instantiate(commandBarPrefab, 
                                            Vector3.zero, 
                                            Quaternion.identity) as GameObject);
                }
                commandBars[i].name = mostCommonCommands[i];
                commandBars[i].transform.parent = commandGraphHolder.transform;
                commandBars[i].transform.localPosition = new Vector3(0, -i * 40, 0);

                Transform bar = commandBars[i].transform.Find("bar");
                Transform count = commandBars[i].transform.Find("count");
                Transform label = commandBars[i].transform.Find("label");

                label.transform.GetComponent<Text>().text = "\"" + mostCommonCommands[i] + "\"";
                if(setCount) {
                    bar.GetComponent<RectTransform>().sizeDelta = new Vector2(15 + Mathf.Atan(int.Parse(mostCommonCommandCounts[i]) / 100f) * 205, 30);
                    count.GetComponent<Text>().text = mostCommonCommandCounts[i];
                }

                if (i == 0) {
                    bar.GetComponent<RawImage>().color = colors["green"];
                }
                else {
                    bar.GetComponent<RawImage>().color = colors["red"];
                }
            }
        } catch {
            print("ERROR in refresh command graph");
        }
    }


    private void CheckForMessage() {
        timer = MESSAGE_CHECK_TIMER;
        CheckForEnd();
        CheckForCommands();   
    }


    void CheckForCommands() {
        mostCommonCommands = dbHandler.ReadFromDB<string[]>("mostCommonCommands");
        mostCommonCommandCounts = dbHandler.ReadFromDB<string[]>("mostCommonCommandCounts");
    }


    void CheckForRewardValues() {

        reward = dbHandler.ReadFromDB<int>("reward");
        punish = dbHandler.ReadFromDB<int>("punish");

        if(!command.Equals("none")) {
            yesSignal.rectTransform.sizeDelta = new Vector2(reward * 1.25f, 30);//rectTransform.localScale = new Vector3(1, reward * 3, 1);
            noSignal.rectTransform.sizeDelta = new Vector2(punish * 3, 30);
        }
        else {
            yesSignal.rectTransform.sizeDelta = Vector2.zero;
            noSignal.rectTransform.sizeDelta = Vector2.zero;
        }
    }


    void CheckForEnd() {
        endRun = dbHandler.ReadFromDB<bool>("nextRobot");
        if (endRun) {
            dbHandler.WriteToDB<bool>("nextRobot", false);
        }
        //string path = Directory.GetCurrentDirectory() + "\\twitch plays\\endrun.txt";
        //endRun = File.Exists(path);
        //if (endRun)
        //{
        //    File.Delete(path);
        //    print("deleting file");
        //   // System.Threading.Thread.Sleep(500);
        //}
        //print(endRun);
    }

    string ColorToHex(Color32 color) {
        string hexValue = color.r.ToString("X2") + color.g.ToString("X2") + color.b.ToString("X2");
        return hexValue;
    }


    void GetActuationCoefficients(float[,] coeffs) {

        for (int i = 0; i < numJoints; i++)
        {
            coeffs[i, 0] = Random.Range(.2f, 2f); //amplitude
            coeffs[i, 1] = Random.Range(.15f, .3f); //period
            coeffs[i, 2] = Random.Range(-3.14159f, 3.14159f); //phase offset
        }

    }


    void Print2DArray(float[,] array) {
        foreach(float value in array) {
            print(value);
        }
    }

}


